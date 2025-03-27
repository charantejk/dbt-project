import React, { useState } from 'react';
import { Card, Descriptions, Table, Tag, Space, Tabs, Button, message, Tooltip, Typography } from 'antd';
import { Link } from 'react-router-dom';
import DescriptionEdit from './DescriptionEdit';
import { DatabaseOutlined, FileOutlined, FolderOutlined, RobotOutlined, ColumnHeightOutlined } from '@ant-design/icons';
import { refreshModelMetadata } from '../services/api';
import ColumnSuggestions from './ColumnSuggestions';

const { TabPane } = Tabs;
const { Text } = Typography;

interface Column {
  id?: any;
  name: string;
  type: string;
  description: string | null;
  ai_description?: string | null;
  user_edited?: boolean;
  isPrimaryKey?: boolean;
  isForeignKey?: boolean;
}

interface Model {
  id: string;
  name: string;
  project: string;
  description: string | null;
  ai_description?: string | null;
  user_edited?: boolean;
  columns: Column[];
  sql: string | null;
  file_path?: string;
  materialized?: string;
  schema?: string;
  database?: string;
}

interface ModelDetailViewProps {
  model: Model;
  onDescriptionUpdated: () => void;
}

const ModelDetailView: React.FC<ModelDetailViewProps> = ({ model, onDescriptionUpdated }) => {
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);

  const handleRefreshMetadata = async () => {
    try {
      setRefreshing(true);
      message.loading({ content: 'Refreshing AI descriptions...', key: 'refresh' });
      await refreshModelMetadata(model.id);
      message.success({ content: 'AI descriptions refreshed successfully!', key: 'refresh' });
      // Trigger refresh of the parent component
      onDescriptionUpdated();
    } catch (error) {
      console.error('Error refreshing model metadata:', error);
      message.error({ content: 'Failed to refresh AI descriptions', key: 'refresh' });
    } finally {
      setRefreshing(false);
    }
  };

  const handleAddColumn = async (column: any) => {
    try {
      // Make API call to add the column
      const response = await fetch(`/api/models/${model.id}/columns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(column),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to add column: ${response.statusText}`);
      }
      
      // Update the UI
      onDescriptionUpdated();
    } catch (error) {
      console.error('Error adding column:', error);
      message.error('Failed to add column');
    }
  };

  // Format file path for display with highlighting the filename
  const formatFilePath = (path: string) => {
    if (!path || path === 'N/A') return <Text>N/A</Text>;
    
    const parts = path.split('/');
    const fileName = parts.pop() || '';
    const directory = parts.join('/');
    
    return (
      <div className="file-path-display">
        <FolderOutlined style={{ marginRight: '8px' }} />
        <span className="directory-path">{directory}/</span>
        <span className="file-name">{fileName}</span>
      </div>
    );
  };

  const columnColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: '20%',
      render: (text: string, record: Column) => (
        record.id ? <Link to={`/columns/${record.id}`}>{text}</Link> : text
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: '15%',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: '55%',
      render: (_: any, record: Column) => (
        <DescriptionEdit
          entityType="column"
          entityId={`${model?.id}:${record.name}`}
          description={record.description}
          aiDescription={record.ai_description || null}
          userEdited={record.user_edited}
          onDescriptionUpdated={onDescriptionUpdated}
        />
      ),
    },
    {
      title: 'Keys',
      key: 'keys',
      width: '10%',
      render: (_: any, record: Column) => (
        <Space>
          {record.isPrimaryKey && <Tag color="green">PK</Tag>}
          {record.isForeignKey && <Tag color="blue">FK</Tag>}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card 
        style={{ marginBottom: '16px' }}
        title={
          <Space size="large">
            <Space>
              <FileOutlined />
              <Text strong>File:</Text> 
              {formatFilePath(model.file_path || 'N/A')}
            </Space>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="Refresh AI descriptions for this model and its columns">
              <Button 
                icon={<RobotOutlined />} 
                onClick={handleRefreshMetadata}
                loading={refreshing}
                type="primary"
              >
                Refresh AI Descriptions
              </Button>
            </Tooltip>
            <Tooltip title="Toggle column suggestions">
              <Button 
                icon={<ColumnHeightOutlined />} 
                onClick={() => setShowSuggestions(!showSuggestions)}
                type={showSuggestions ? "default" : "primary"}
              >
                {showSuggestions ? "Hide Suggestions" : "Show Column Suggestions"}
              </Button>
            </Tooltip>
          </Space>
        }
      >
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Project" span={1}>
            <Tag color="blue" icon={<DatabaseOutlined />}>
              {model.project}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Schema" span={1}>{model.schema || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Materialized" span={1}>{model.materialized || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Columns" span={1}>{model.columns?.length || 0}</Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>
            <DescriptionEdit
              entityType="model"
              entityId={model.id}
              description={model.description}
              aiDescription={model.ai_description || null}
              userEdited={model.user_edited}
              onDescriptionUpdated={onDescriptionUpdated}
            />
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {showSuggestions && (
        <Card style={{ marginBottom: '16px' }}>
          <ColumnSuggestions 
            modelName={model.name}
            existingColumns={model.columns.map(col => col.name)}
            onAddColumn={handleAddColumn}
          />
        </Card>
      )}

      <Tabs defaultActiveKey="columns" type="card">
        <TabPane tab="Columns" key="columns">
          <Table 
            dataSource={model.columns || []} 
            columns={columnColumns} 
            rowKey="name" 
            pagination={{ pageSize: 20 }} 
          />
        </TabPane>
        
        <TabPane tab="SQL" key="sql">
          <pre className="sql-code">{model.sql || 'No SQL available'}</pre>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default ModelDetailView; 