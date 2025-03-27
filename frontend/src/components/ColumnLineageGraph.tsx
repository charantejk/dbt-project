import React, { useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ColumnWithRelations, Column } from '../types';
import { Typography, Space, Tag } from 'antd';

const { Text } = Typography;

interface ColumnLineageGraphProps {
  columns: ColumnWithRelations[];
  selectedColumnId: string;
}

const nodeWidth = 200;
const nodeHeight = 60;

const getNodeId = (column: ColumnWithRelations | Column): string => {
  return column.id ? column.id.toString() : `${column.model_name || ''}-${column.name}`;
};

const ColumnLineageGraph: React.FC<ColumnLineageGraphProps> = ({ columns, selectedColumnId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    // Find selected column
    const selectedColumn = columns.find(col => getNodeId(col) === selectedColumnId);
    if (!selectedColumn) {
      console.error(`Selected column ${selectedColumnId} not found in data`);
      return;
    }

    const graphNodes: Node[] = [];
    const graphEdges: Edge[] = [];
    const addedNodeIds = new Set<string>();

    // Helper function to create a column node
    const createColumnNode = (
      column: ColumnWithRelations | Column,
      position: { x: number; y: number },
      isSelected: boolean = false
    ): Node => {
      // Extract model information from the column
      const modelName = column.model_name || 'Unknown Model';
      const projectName = column.project_name || 'Unknown Project';
      const dataType = column.data_type || '';
      const isPrimaryKey = column.is_primary_key || false;
      
      // Generate project-based color
      const hashCode = projectName.split('').reduce((a: number, b: string) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
      }, 0);
      
      const hue = Math.abs(hashCode % 360);
      const backgroundColor = isSelected 
        ? `hsl(${hue}, 70%, 85%)` 
        : `hsl(${hue}, 50%, 95%)`;
      const borderColor = isSelected 
        ? `hsl(${hue}, 70%, 50%)` 
        : `hsl(${hue}, 50%, 80%)`;
      
      return {
        id: getNodeId(column),
        type: 'default',
        position,
        data: {
          label: (
            <div style={{ padding: '5px' }}>
              <div style={{ fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {column.name}
              </div>
              <div style={{ fontSize: '0.8em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {modelName}
              </div>
            </div>
          ),
          modelName,
          projectName,
          dataType,
          isPrimaryKey,
          isSelected
        },
        style: {
          width: nodeWidth,
          height: nodeHeight,
          background: backgroundColor,
          border: `2px solid ${borderColor}`,
          borderRadius: '5px',
          boxShadow: isSelected ? '0 0 10px rgba(0, 0, 0, 0.2)' : 'none',
        },
      };
    };

    // Add selected column in the center
    graphNodes.push(createColumnNode(selectedColumn, { x: 0, y: 0 }, true));
    addedNodeIds.add(getNodeId(selectedColumn));

    // Add upstream columns
    if (selectedColumn.upstream_columns) {
      selectedColumn.upstream_columns.forEach((upstreamCol, index) => {
        const colId = getNodeId(upstreamCol);
        if (!addedNodeIds.has(colId)) {
          const x = -300;
          const y = -150 + index * 100;
          graphNodes.push(createColumnNode(upstreamCol, { x, y }));
          addedNodeIds.add(colId);
        }

        // Add edge from upstream to selected
        graphEdges.push({
          id: `edge-${colId}-${getNodeId(selectedColumn)}`,
          source: colId,
          target: getNodeId(selectedColumn),
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#1890ff' },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 15,
            height: 15,
            color: '#1890ff',
          },
        });
      });
    }

    // Add downstream columns
    if (selectedColumn.downstream_columns) {
      selectedColumn.downstream_columns.forEach((downstreamCol, index) => {
        const colId = getNodeId(downstreamCol);
        if (!addedNodeIds.has(colId)) {
          const x = 300;
          const y = -150 + index * 100;
          graphNodes.push(createColumnNode(downstreamCol, { x, y }));
          addedNodeIds.add(colId);
        }

        // Add edge from selected to downstream
        graphEdges.push({
          id: `edge-${getNodeId(selectedColumn)}-${colId}`,
          source: getNodeId(selectedColumn),
          target: colId,
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#1890ff' },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 15,
            height: 15,
            color: '#1890ff',
          },
        });
      });
    }

    setNodes(graphNodes);
    setEdges(graphEdges);
  }, [columns, selectedColumnId, setNodes, setEdges]);

  // Show legend explaining the graph
  const renderLegend = () => (
    <div style={{ marginBottom: '15px' }}>
      <Space>
        <Text>Legend:</Text>
        <Tag color="#e6f7ff">Selected Column</Tag>
        <Tag color="#f0f5ff">Related Columns</Tag>
        <Text type="secondary">Arrows indicate data flow direction</Text>
      </Space>
    </div>
  );

  return (
    <>
      {renderLegend()}
      <div style={{ width: '100%', height: '400px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          attributionPosition="bottom-right"
        >
          <Controls />
          <MiniMap />
          <Background color="#f5f5f5" />
        </ReactFlow>
      </div>
    </>
  );
};

export default ColumnLineageGraph; 