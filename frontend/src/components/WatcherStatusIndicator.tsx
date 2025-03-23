import React, { useEffect, useState } from 'react';
import { Badge, Switch, Tooltip, Typography, Space } from 'antd';
import { SyncOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { getWatcherStatus, toggleWatcher } from '../services/api';

const { Text } = Typography;

interface WatcherStatus {
  active: boolean;
  watching_directory: string;
  watch_interval_seconds: number;
  watched_files_count: number;
  last_refresh_time: string | null;
}

const WatcherStatusIndicator: React.FC = () => {
  const [status, setStatus] = useState<WatcherStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  const fetchStatus = async () => {
    try {
      const result = await getWatcherStatus();
      setStatus(result);
    } catch (error) {
      console.error('Error fetching watcher status:', error);
    }
  };
  
  useEffect(() => {
    fetchStatus();
    
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);
  
  const handleToggle = async (checked: boolean) => {
    setLoading(true);
    try {
      await toggleWatcher(checked);
      // Refresh status
      await fetchStatus();
    } catch (error) {
      console.error('Error toggling watcher:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!status) {
    return null;
  }
  
  const getStatusDisplay = () => {
    if (status.active) {
      return (
        <Badge 
          status="processing" 
          text={
            <Space>
              <Text type="success">Auto-refresh active</Text>
              <SyncOutlined spin style={{ color: '#52c41a' }} />
            </Space>
          } 
        />
      );
    }
    return <Badge status="default" text="Auto-refresh off" />;
  };
  
  const tooltipContent = () => (
    <div>
      <p>
        <strong>Status:</strong> {status.active ? 'Active' : 'Inactive'}
      </p>
      <p>
        <strong>Watching:</strong> {status.watching_directory}
      </p>
      <p>
        <strong>Check interval:</strong> {status.watch_interval_seconds} seconds
      </p>
      <p>
        <strong>Files monitored:</strong> {status.watched_files_count}
      </p>
      {status.last_refresh_time && (
        <p>
          <strong>Last refresh:</strong> {new Date(status.last_refresh_time).toLocaleString()}
        </p>
      )}
    </div>
  );
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <Tooltip title={tooltipContent()}>
        {getStatusDisplay()}
      </Tooltip>
      <Tooltip title={status.active ? 'Turn off auto-refresh' : 'Turn on auto-refresh'}>
        <Switch 
          size="small" 
          checked={status.active} 
          onChange={handleToggle}
          loading={loading}
        />
      </Tooltip>
    </div>
  );
};

export default WatcherStatusIndicator; 