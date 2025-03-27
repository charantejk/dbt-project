import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Tabs, Table, Typography, Tag, Space, Tooltip, Button } from 'antd';
import { ArrowLeftOutlined, CodeOutlined, FileOutlined, TableOutlined, BranchesOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { Model, Column, ColumnWithRelations } from '../types';
import ColumnLineageGraph from './ColumnLineageGraph';
import RelatedModels from './RelatedModels';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface ColumnTableProps {
  columns: Column[];
  onViewColumnLineage?: (columnId: string) => void;
}

const ColumnTable: React.FC<ColumnTableProps> = ({ columns, onViewColumnLineage }) => {
  const dataColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Column) => (
        <Space>
          <Text strong>{text}</Text>
          {onViewColumnLineage && (
            <Button 
              type="link" 
              size="small" 
              icon={<BranchesOutlined />} 
              onClick={() => onViewColumnLineage(record.id.toString())}
            />
          )}
        </Space>
      ),
    },
    {
      title: 'Data Type',
      dataIndex: 'data_type',
      key: 'data_type',
      render: (text: string) => <Tag>{text}</Tag>,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
  ];

  return (
    <Table 
      dataSource={columns} 
      columns={dataColumns} 
      rowKey={(record) => record.id.toString()}
      pagination={false}
    />
  );
};

const ModelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [model, setModel] = useState<Model | null>(null);
  const [relatedModels, setRelatedModels] = useState<{ upstream: Model[], downstream: Model[] }>({ 
    upstream: [], 
    downstream: [] 
  });
  const [columnRelations, setColumnRelations] = useState<ColumnWithRelations[]>([]);
  const [selectedColumnId, setSelectedColumnId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModelDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch model details
        const modelResponse = await fetch(`http://localhost:8000/api/models/${id}`);
        if (!modelResponse.ok) {
          throw new Error(`Error fetching model: ${modelResponse.statusText}`);
        }
        const modelData = await modelResponse.json();
        setModel(modelData);

        // Fetch related models (lineage)
        const lineageResponse = await fetch(`http://localhost:8000/api/models/${id}/lineage`);
        if (!lineageResponse.ok) {
          throw new Error(`Error fetching lineage: ${lineageResponse.statusText}`);
        }
        const lineageData = await lineageResponse.json();
        setRelatedModels(lineageData);

        // Fetch column-level lineage
        const columnLineageResponse = await fetch(`http://localhost:8000/api/models/${id}/column-lineage`);
        if (!columnLineageResponse.ok) {
          throw new Error(`Error fetching column lineage: ${columnLineageResponse.statusText}`);
        }
        const columnLineageData = await columnLineageResponse.json();
        setColumnRelations(columnLineageData.columns || []);

      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchModelDetails();
    }
  }, [id]);

  const handleViewColumnLineage = (columnId: string) => {
    setSelectedColumnId(columnId);
  };

  const renderProjectTag = () => {
    if (!model) return null;
    
    const projectName = model.project || model.project_name;
    if (!projectName) return null;
    
    // Create a pseudo-random but consistent color for the project tag
    const hashCode = projectName.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    
    // Use the hash to generate an HSL color
    const hue = Math.abs(hashCode % 360); // 0-359 degrees
    const color = `hsl(${hue}, 70%, 50%)`;
    
    return (
      <Tag color={color} style={{ marginBottom: 16 }}>
        {projectName}
      </Tag>
    );
  };

  if (loading) {
    return <div>Loading model details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!model) {
    return <div>Model not found</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Link to="/">
            <Button icon={<ArrowLeftOutlined />} style={{ marginBottom: 16 }}>
              Back to Models
            </Button>
          </Link>
          {renderProjectTag()}
          <Title level={2}>{model.name}</Title>
          {model.description && (
            <Paragraph>{model.description}</Paragraph>
          )}
        </div>

        <Tabs defaultActiveKey="columns">
          <TabPane
            tab={
              <span>
                <TableOutlined />
                Columns
              </span>
            }
            key="columns"
          >
            <Card>
              {model.columns && model.columns.length > 0 ? (
                <ColumnTable 
                  columns={model.columns} 
                  onViewColumnLineage={handleViewColumnLineage}
                />
              ) : (
                <Text type="secondary">No columns found for this model</Text>
              )}
            </Card>
          </TabPane>

          <TabPane
            tab={
              <span>
                <BranchesOutlined />
                Lineage
              </span>
            }
            key="lineage"
          >
            <Card>
              <RelatedModels 
                upstream={relatedModels.upstream} 
                downstream={relatedModels.downstream}
              />
            </Card>
          </TabPane>

          <TabPane
            tab={
              <span>
                <CodeOutlined />
                SQL
              </span>
            }
            key="sql"
          >
            <Card>
              {model.sql ? (
                <SyntaxHighlighter language="sql" style={docco}>
                  {model.sql}
                </SyntaxHighlighter>
              ) : (
                <Text type="secondary">No SQL available for this model</Text>
              )}
            </Card>
          </TabPane>

          <TabPane
            tab={
              <span>
                <FileOutlined />
                Metadata
              </span>
            }
            key="metadata"
          >
            <Card>
              <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', rowGap: '10px' }}>
                <Text strong>Model ID:</Text>
                <Text>{model.id}</Text>
                
                <Text strong>Project:</Text>
                <Text>{model.project || model.project_name || 'Unknown'}</Text>
                
                <Text strong>File Path:</Text>
                <Text>{model.file_path || 'Not available'}</Text>
                
                <Text strong>Column Count:</Text>
                <Text>{model.columns?.length || 0}</Text>
                
                {model.materialized && (
                  <>
                    <Text strong>Materialization:</Text>
                    <Text>{model.materialized}</Text>
                  </>
                )}
              </div>
            </Card>
          </TabPane>
        </Tabs>

        {selectedColumnId && (
          <Card 
            title={
              <Space>
                <BranchesOutlined />
                <span>Column Lineage</span>
                <Tooltip title="This visualization shows how columns are related across models">
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                </Tooltip>
              </Space>
            }
            extra={
              <Button type="link" onClick={() => setSelectedColumnId(null)}>
                Close
              </Button>
            }
          >
            <ColumnLineageGraph 
              columns={columnRelations}
              selectedColumnId={selectedColumnId}
            />
          </Card>
        )}
      </Space>
    </div>
  );
};

export default ModelDetail; 