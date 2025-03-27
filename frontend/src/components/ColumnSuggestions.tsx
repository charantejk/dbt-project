import React, { useState } from 'react';
import { Card, List, Button, message, Tag, Spin } from 'antd';
import { PlusOutlined, SyncOutlined } from '@ant-design/icons';

interface ColumnSuggestion {
  name: string;
  type: string;
  description: string;
}

interface ColumnSuggestionsProps {
  modelName: string;
  existingColumns: string[];
  onAddColumn: (column: ColumnSuggestion) => void;
}

const ColumnSuggestions: React.FC<ColumnSuggestionsProps> = ({ 
  modelName, 
  existingColumns, 
  onAddColumn 
}) => {
  const [suggestions, setSuggestions] = useState<ColumnSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);

  const handleGenerateSuggestions = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/models/suggest-columns', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: modelName,
          existing_columns: existingColumns
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to generate suggestions: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSuggestions(data);
    } catch (error) {
      console.error('Error generating suggestions:', error);
      message.error('Failed to generate suggestions');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDescription = async (column: ColumnSuggestion) => {
    try {
      setSelectedColumn(column.name);
      const response = await fetch('/api/models/suggest-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: modelName,
          column_name: column.name,
          column_type: column.type
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to generate description: ${response.statusText}`);
      }
      
      const data = await response.json();
      column.description = data.description;
      setSuggestions([...suggestions]);
    } catch (error) {
      console.error('Error generating description:', error);
      message.error('Failed to generate description');
    } finally {
      setSelectedColumn(null);
    }
  };

  const handleAddColumn = async (column: ColumnSuggestion) => {
    try {
      onAddColumn(column);
      message.success(`Added column: ${column.name}`);
    } catch (error) {
      console.error('Error adding column:', error);
      message.error('Failed to add column');
    }
  };

  return (
    <Card 
      title="Suggested Columns" 
      extra={
        <Button 
          type="primary" 
          onClick={handleGenerateSuggestions}
          loading={loading}
          icon={<SyncOutlined />}
        >
          Generate Suggestions
        </Button>
      }
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin tip="Generating suggestions..." />
        </div>
      ) : suggestions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <p>No suggestions yet. Click "Generate Suggestions" to get column recommendations.</p>
        </div>
      ) : (
        <List
          dataSource={suggestions}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => handleAddColumn(item)}
                >
                  Add
                </Button>
              ]}
            >
              <List.Item.Meta
                title={
                  <span>
                    {item.name} <Tag color="blue">{item.type}</Tag>
                  </span>
                }
                description={
                  <div>
                    {item.description ? (
                      item.description
                    ) : (
                      <Button 
                        type="link" 
                        onClick={() => handleGenerateDescription(item)}
                        loading={selectedColumn === item.name}
                      >
                        Generate Description
                      </Button>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default ColumnSuggestions; 