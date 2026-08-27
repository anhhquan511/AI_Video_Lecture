import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { videoApi } from '../services/api';
import { Button, Card, Typography, Spin, Row, Col, Timeline, Tag, Empty, Breadcrumb } from 'antd';
import { DownloadOutlined, ArrowLeftOutlined, CopyOutlined, FilePdfOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const VideoDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const getFileName = (path) => {
      if (!path) return '---';
      return path.split(/[/\\]/).pop();
  };

  // Fetch dữ liệu chi tiết
  const { data: project, isLoading } = useQuery({
    queryKey: ['video', id],
    queryFn: async () => {
      const res = await videoApi.getVideoDetail(id);
      return res.data;
    },
  });

  if (isLoading) return <div className="flex justify-center mt-20"><Spin size="large" /></div>;
  if (!project) return <Empty description="Không tìm thấy video" />;

  const videoUrl = project.final_video_url 
    ? `http://localhost:8000${project.final_video_url}` 
    : null;

  return (
    <div className="p-4">
      {/* 1. Thanh điều hướng & Header */}
      <div className="mb-6">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} className="mb-4">
          Quay lại
        </Button>
        
        <div className="flex justify-between items-start">
          <div>
            <Title level={3} style={{ margin: 0 }}>{project.topic_prompt || project.topic}</Title>
            <div className="mt-2 text-gray-500">
                <FilePdfOutlined /> Tài liệu gốc: <Text strong>{getFileName(project.source_file)}</Text>
            </div>
            <Text type="secondary">Job ID: {project.job_id}</Text> <CopyOutlined className="cursor-pointer ml-2" />
          </div>
          
          {videoUrl && (
            <Button 
              type="primary" 
              icon={<DownloadOutlined />} 
              size="large"
              onClick={() => window.open(videoUrl, '_blank')}
            >
              Tải Video
            </Button>
          )}
        </div>
      </div>

      <Row gutter={24}>
        {/* 2. Cột Trái: Video Player */}
        <Col span={14}>
          <Card className="shadow-lg border-0" bodyStyle={{ padding: 0 }}>
            {videoUrl ? (
              <video 
                controls 
                autoPlay 
                className="w-full h-auto rounded-t-lg"
                style={{ maxHeight: '500px', backgroundColor: '#000' }}
              >
                <source src={videoUrl} type="video/mp4" />
                Trình duyệt của bạn không hỗ trợ thẻ video.
              </video>
            ) : (
              <div className="h-64 flex items-center justify-center bg-gray-100 text-gray-400">
                Video đang xử lý hoặc bị lỗi.
              </div>
            )}
            
            <div className="p-4">
               <Title level={5}>Thông tin kỹ thuật</Title>
               <div className="flex gap-2">
                 <Tag color="blue">Model: Gemini 1.5 Flash</Tag>
                 <Tag color="cyan">TTS: Edge-TTS</Tag>
                 <Tag color="geekblue">RAG: ChromaDB</Tag>
               </div>
            </div>
          </Card>
        </Col>

        
        <Col span={10}>
          <Card 
            title="Kịch bản chi tiết (AI Generated)" 
            className="h-full shadow-md overflow-y-auto"
            style={{ maxHeight: '600px', overflowY: 'auto' }}
          >
            {project.script_scenes && project.script_scenes.length > 0 ? (
              <Timeline>
                {project.script_scenes.map((scene, index) => (
                  <Timeline.Item key={index} color="blue">
                    <Text strong>Cảnh {index + 1}</Text>
                    
                    {/* Hiển thị nội dung Slide nếu có */}
                    {scene.slide_content && (
                       <div className="bg-blue-50 p-2 rounded mb-2 mt-1 border border-blue-100">
                          <Text type="secondary" style={{fontSize: '12px'}}>🖥️ SLIDE: {scene.slide_content.title}</Text>
                       </div>
                    )}

                    {/* Lời thoại */}
                    <Paragraph 
                      className="text-gray-600 mt-1 text-justify" 
                      style={{ fontSize: '14px' }}
                      ellipsis={{ rows: 3, expandable: true, symbol: 'Xem thêm' }}
                    >
                      "{scene.text}"
                    </Paragraph>
                  </Timeline.Item>
                ))}
              </Timeline>
            ) : (
              <Empty description="Chưa có kịch bản" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default VideoDetail;