import React from 'react';
import { Card, Tag, Empty, Divider, Button, Tooltip } from 'antd';
import { Model } from '../types';
import { ArrowRightOutlined, ArrowLeftOutlined, LinkOutlined, DatabaseOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

// Create a project color map function to consistently color project tags
const getProjectColor = (projectName: string): string => {
  // Simple hash function to generate a consistent color for a project name
  const hash = projectName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const colors = ['magenta', 'red', 'volcano', 'orange', 'gold', 'lime', 'green', 'cyan', 'blue', 'geekblue', 'purple'];
  return colors[hash % colors.length];
};

interface RelatedModelsProps {
  model?: Model;
  upstream: Model[];
  downstream: Model[];
}

const RelatedModels: React.FC<RelatedModelsProps> = ({
  model,
  upstream,
  downstream
}) => {
  // Check if there are any cross-project relationships
  const modelProject = model?.project || model?.project_name || '';
  const hasCrossProjectUpstream = upstream.some(m => {
    const upstreamProject = m.project || m.project_name || '';
    return upstreamProject !== modelProject && modelProject !== '';
  });
  
  const hasCrossProjectDownstream = downstream.some(m => {
    const downstreamProject = m.project || m.project_name || '';
    return downstreamProject !== modelProject && modelProject !== '';
  });

  // Group related models by project
  const groupModelsByProject = (models: Model[]) => {
    const groups: Record<string, Model[]> = {};

    models.forEach(m => {
      const projectName = m.project || m.project_name || 'Unknown';
      if (!groups[projectName]) {
        groups[projectName] = [];
      }
      groups[projectName].push(m);
    });

    return groups;
  };

  const upstreamByProject = groupModelsByProject(upstream);
  const downstreamByProject = groupModelsByProject(downstream);

  return (
    <div className="related-models-container">
      {/* Upstream Models Section */}
      <div className="related-models-section">
        <h3 className="section-title">
          <Tooltip title="Models that feed into this model">
            <span>
              Upstream <ArrowRightOutlined />
            </span>
          </Tooltip>
          {hasCrossProjectUpstream && (
            <Tag className="cross-project-tag" color="blue">
              Cross-Project
            </Tag>
          )}
        </h3>

        {upstream.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No upstream models"
          />
        ) : (
          <div className="related-models-list">
            {Object.entries(upstreamByProject).map(([projectName, models]) => (
              <div key={`upstream-${projectName}`} className="project-model-group">
                {/* Show project badge if it's a different project */}
                {projectName !== modelProject && modelProject !== '' && (
                  <div className="cross-project-header">
                    <Tag color={getProjectColor(projectName)} icon={<DatabaseOutlined />}>
                      {projectName}
                    </Tag>
                  </div>
                )}

                <div className="model-list">
                  {models.map(relatedModel => (
                    <Card
                      key={`upstream-${relatedModel.id}`}
                      size="small"
                      className="related-model-card"
                      title={
                        <Link to={`/models/${relatedModel.id}`}>
                          <Tag
                            className="related-model-tag"
                            icon={projectName !== modelProject && modelProject !== '' ? <LinkOutlined /> : null}
                            color={projectName !== modelProject && modelProject !== '' ? 'blue' : 'default'}
                          >
                            {relatedModel.name}
                          </Tag>
                        </Link>
                      }
                    >
                      <div className="model-description">
                        {relatedModel.description || "No description"}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Divider />

      {/* Downstream Models Section */}
      <div className="related-models-section">
        <h3 className="section-title">
          <Tooltip title="Models that are derived from this model">
            <span>
              <ArrowLeftOutlined /> Downstream
            </span>
          </Tooltip>
          {hasCrossProjectDownstream && (
            <Tag className="cross-project-tag" color="green">
              Cross-Project
            </Tag>
          )}
        </h3>

        {downstream.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No downstream models"
          />
        ) : (
          <div className="related-models-list">
            {Object.entries(downstreamByProject).map(([projectName, models]) => (
              <div key={`downstream-${projectName}`} className="project-model-group">
                {/* Show project badge if it's a different project */}
                {projectName !== modelProject && modelProject !== '' && (
                  <div className="cross-project-header">
                    <Tag color={getProjectColor(projectName)} icon={<DatabaseOutlined />}>
                      {projectName}
                    </Tag>
                  </div>
                )}

                <div className="model-list">
                  {models.map(relatedModel => (
                    <Card
                      key={`downstream-${relatedModel.id}`}
                      size="small"
                      className="related-model-card"
                      title={
                        <Link to={`/models/${relatedModel.id}`}>
                          <Tag
                            className="related-model-tag"
                            icon={projectName !== modelProject && modelProject !== '' ? <LinkOutlined /> : null}
                            color={projectName !== modelProject && modelProject !== '' ? 'green' : 'default'}
                          >
                            {relatedModel.name}
                          </Tag>
                        </Link>
                      }
                    >
                      <div className="model-description">
                        {relatedModel.description || "No description"}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RelatedModels; 