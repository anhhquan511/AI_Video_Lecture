import React, { useState } from 'react';
import { Table, Tag, Button, Space, Card, Typography, Row, Col, Statistic, Input, Popconfirm, notification } from 'antd';
import { 
  PlayCircleOutlined, ReloadOutlined, 
  CheckCircleOutlined, ClockCircleOutlined, 
  FilePdfOutlined, DeleteOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { videoApi } from '../services/api';
import { useNavigate } from 'react-router-dom';

const { Search } = Input;

const getFileName = (path) => {
  try {
      if (!path) return null;
      if (typeof path !== 'string') return 'File ???';
      // Xử lý đường dẫn Windows (\) và Linux (/)
      const cleanPath = path.replace(/\\/g, '/');
      return cleanPath.split('/').pop();
  } catch (e) {
      return 'Lỗi tên';
  }
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState('');

  const { data: videos = [], isLoading, refetch } = useQuery({
    queryKey: ['videos'],
    queryFn: async () => {
      const res = await videoApi.getAllVideos();
      return res.data;
    },
    refetchInterval: 5000,
  });

  const totalVideos = videos.length;
  const completedVideos = videos.filter(v => v.status === 'COMPLETED').length;
  const processingVideos = videos.filter(v => v.status !== 'COMPLETED' && v.status !== 'FAILED').length;

  const filteredData = videos.filter(item => 
    item.topic?.toLowerCase().includes(searchText.toLowerCase())
  );

  //xu ly xoa
  const handleDelete = async (jobId) => {
    try {
      await videoApi.deleteVideo(jobId);
      notification.success({ message: 'Đã xóa video thành công!' });
      refetch(); // Tải lại bảng ngay lập tức
    } catch (error) {
      notification.error({ message: 'Lỗi khi xóa video' });
    }
  };

  const columns = [
    {
      title: 'Chủ đề bài giảng',
      dataIndex: 'topic',
      key: 'topic',
      render: (text) => <span style={{ fontWeight: 600, fontSize: '15px' }}>{text}</span>,
    },
    {
      title: 'Tài liệu nguồn',
      dataIndex: 'source_file',
      key: 'source_file',
      render: (text) => {
        // Bây giờ gọi hàm này thoải mái vì nó nằm ở global scope
        const fileName = getFileName(text);
        
        if (!fileName) return <Tag>---</Tag>;
        
        return (
            <Tag color="geekblue" style={{ display: 'flex', alignItems: 'center', width: 'fit-content' }}>
               <FilePdfOutlined style={{ marginRight: 5 }} /> 
               <span style={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                 {fileName}
               </span>
            </Tag>
        );
      },
    },
    {
      title: 'Tiến độ',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        let color = 'default';
        let icon = <ClockCircleOutlined />;
        let textLabel = status;

        if (status === 'COMPLETED') {
            color = 'success'; 
            icon = <CheckCircleOutlined />;
            textLabel = 'Hoàn thành';
        } else if (status === 'FAILED') {
            color = 'error';
            textLabel = 'Lỗi';
        } else if (status === 'PROCESSING_SCRIPT') {
            color = 'processing';
            textLabel = 'Viết kịch bản...';
        } else if (status === 'RENDERING_VIDEO') {
            color = 'warning';
            textLabel = 'Đang dựng phim...';
        }

        return <Tag icon={icon} color={color}>{textLabel}</Tag>;
      },
    },
    {
      title: 'Hành động',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          {record.status === 'COMPLETED' && (
            <Button 
              type="primary" 
              ghost
              icon={<PlayCircleOutlined />} 
              onClick={() => navigate(`/video/${record.job_id}`)}
            >
              Xem ngay
            </Button>
          )}

          <Popconfirm
            title="Bạn có chắc chắn muốn xóa?"
            description="Video và dữ liệu sẽ bị mất vĩnh viễn."
            onConfirm={() => handleDelete(record.job_id)}
            okText="Xóa luôn"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
          >
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
          
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Thống kê - Đã sửa lỗi warning valueStyle */}
      <Row gutter={16} className="mb-6">
        <Col span={8}>
          <Card className="shadow-sm">
            <Statistic 
              title="Tổng số bài giảng" 
              value={totalVideos} 
              prefix={<PlayCircleOutlined />} 
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="shadow-sm">
            <Statistic 
              title="Đã hoàn thành" 
              value={completedVideos} 
              prefix={<CheckCircleOutlined />} 
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="shadow-sm">
            <Statistic 
              title="Đang xử lý" 
              value={processingVideos} 
              prefix={<ClockCircleOutlined />} 
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Bảng dữ liệu */}
      <Card className="shadow-md" title="Danh sách bài giảng gần đây">
        <div className="flex justify-between mb-4">
            <Search 
              placeholder="Tìm kiếm chủ đề..." 
              allowClear 
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 300 }} 
            />
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Làm mới</Button>
        </div>

        <Table 
          columns={columns} 
          dataSource={filteredData} 
          rowKey="job_id" 
          loading={isLoading}
          pagination={{ pageSize: 6 }}
        />
      </Card>
    </div>
  );
};

export default Dashboard;