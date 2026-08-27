import React, { useState } from 'react';
import { 
  Form, Input, Button, Upload, Card, Typography, 
  Row, Col, Tabs, notification, Spin, Table, Tag, Radio 
} from 'antd';
import { 
  InboxOutlined, FilePdfOutlined, YoutubeOutlined, 
  ThunderboltOutlined, CloudUploadOutlined, CheckCircleOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query'; // Import thêm useQuery
import { videoApi } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;

const CreateVideo = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [activeTab, setActiveTab] = useState('1'); // State để biết đang ở Tab nào
  const [selectedDoc, setSelectedDoc] = useState(null); // State lưu file chọn từ thư viện
  const navigate = useNavigate();

  // 1. Fetch danh sách tài liệu từ Backend
  const { data: documents = [], isLoading: loadingDocs } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      try {
        const res = await videoApi.getDocuments();
        return res.data;
      } catch (e) {
        return [];
      }
    },
    
    enabled: activeTab === '2', 
  });

  // Xử lý upload file (Tab 1)
  const uploadProps = {
    onRemove: (file) => {
      setFileList([]);
    },
    beforeUpload: (file) => {
      const isPdf = file.type === 'application/pdf';
      if (!isPdf) {
        notification.error({ message: 'Chỉ chấp nhận file PDF!' });
        return Upload.LIST_IGNORE;
      }
      setFileList([file]);
      return false;
    },
    fileList,
  };

  // Cấu hình cột cho bảng Library (Tab 2)
  const columns = [
    {
      title: 'Tên tài liệu',
      dataIndex: 'name',
      key: 'name',
      render: (text) => (
        <span><FilePdfOutlined className="text-red-500 mr-2" />{text}</span>
      ),
    },
    {
      title: 'Kích thước',
      dataIndex: 'size',
      key: 'size',
    },
    {
      title: 'Chọn',
      key: 'action',
      render: (_, record) => (
        <Radio 
          checked={selectedDoc === record.name} 
          onChange={() => setSelectedDoc(record.name)}
        >
          Dùng file này
        </Radio>
      ),
    },
  ];

  const onFinish = async (values) => {
    // 1. Validate đầu vào
    if (activeTab === '1' && fileList.length === 0) {
      notification.warning({ message: 'Vui lòng upload tài liệu PDF!' });
      return;
    }
    if (activeTab === '2' && !selectedDoc) {
      notification.warning({ message: 'Vui lòng chọn một tài liệu từ thư viện!' });
      return;
    }

    setLoading(true);
    try {
      // 2. Chuẩn bị FormData
      const formData = new FormData();
      formData.append('topic', values.topic);

      if (activeTab === '1') {
        formData.append('file', fileList[0]);
      } else {
        formData.append('existing_file_name', selectedDoc);
      }

      // 3. Gửi yêu cầu tạo Video
      const res = await videoApi.createVideo(formData);
      const jobId = res.data.job_id;

      
      let isError = false;
      let attempts = 0;
      
      // Vòng lặp kiểm tra: 3 lần, mỗi lần cách nhau 1.5 giây
      while (attempts < 3) {
         await new Promise(r => setTimeout(r, 1500));
         
         const statusRes = await videoApi.getVideoDetail(jobId);
         const status = statusRes.data.status;
         
         if (status === 'FAILED') {
             isError = true;
             const errorMsg = statusRes.data.error_message || 'Chủ đề không phù hợp với tài liệu.';
             
             notification.error({
                 message: 'Không thể tạo video!',
                 description: errorMsg,
                 duration: 6,
             });
             break;
         }
         attempts++;
      }

      if (!isError) {
          notification.success({
            message: 'Đang xử lý!',
            description: 'Yêu cầu hợp lệ. Đang chuyển về Dashboard để theo dõi...',
          });
          
          setTimeout(() => {
            navigate('/');
          }, 1000);
      }

    } catch (error) {
      console.error(error);
      notification.error({
        message: 'Lỗi kết nối',
        description: error.response?.data?.detail || 'Không thể gửi yêu cầu.',
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Cấu hình các Tabs
  const items = [
    {
      key: '1',
      label: <span><CloudUploadOutlined /> Upload Mới</span>,
      children: (
        <div className="mt-4">
           <Form.Item label="Tài liệu tham khảo (PDF)">
            <Dragger {...uploadProps} style={{ padding: 20, background: '#fafafa' }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">Kéo thả file PDF vào đây</p>
            </Dragger>
          </Form.Item>
        </div>
      ),
    },
    {
      key: '2',
      label: <span><FilePdfOutlined /> Chọn từ Thư viện</span>,
      children: (
        <div className="mt-4">
           <Form.Item label="Danh sách tài liệu đã upload">
             <Table 
               dataSource={documents} 
               columns={columns} 
               rowKey="name"
               loading={loadingDocs}
               pagination={{ pageSize: 5 }}
               size="small"
               bordered
               onRow={(record) => ({
                 onClick: () => setSelectedDoc(record.name),
                 style: { cursor: 'pointer' }
               })}
             />
             {selectedDoc && (
               <div className="mt-2 text-green-600 font-medium">
                 <CheckCircleOutlined /> Đã chọn: {selectedDoc}
               </div>
             )}
           </Form.Item>
        </div>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div className="text-center mb-8">
        <Title level={2}>Tạo bài giảng AI</Title>
        <Paragraph type="secondary" style={{ fontSize: 16 }}>
            Chọn tài liệu và nhập chủ đề để bắt đầu.
        </Paragraph>
      </div>

      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Row gutter={24}>
          <Col span={14}>
              <Card className="shadow-lg">
                  {/* Ô nhập chủ đề luôn hiện ở cả 2 tab */}
                  <Form.Item
                    label="Chủ đề bài giảng"
                    name="topic"
                    rules={[{ required: true, message: 'Vui lòng nhập chủ đề!' }]}
                  >
                    <Input placeholder="Ví dụ: Tổng quan về Triết học..." size="large" />
                  </Form.Item>

                  {/* Khu vực Tabs */}
                  <Tabs 
                    activeKey={activeTab} 
                    onChange={setActiveTab} 
                    items={items} 
                    type="card"
                  />

                  <Form.Item className="mt-6">
                    <Button 
                      type="primary" 
                      htmlType="submit" 
                      size="large" 
                      block 
                      loading={loading}
                      icon={<ThunderboltOutlined />}
                    >
                      {loading ? 'Đang xử lý...' : 'Bắt đầu tạo Video'}
                    </Button>
                  </Form.Item>
              </Card>
          </Col>

          {/* Cột hướng dẫn (Giữ nguyên) */}
          <Col span={10}>
              <Card className="bg-blue-50 border-blue-100" title="Hướng dẫn">
                  <div className="flex flex-col gap-4">
                      <div>
                        <Text strong>Tab Upload Mới:</Text>
                        <div className="text-gray-500 text-sm">Dùng khi bạn có file PDF mới trong máy tính.</div>
                      </div>
                      <div>
                        <Text strong>Tab Thư viện:</Text>
                        <div className="text-gray-500 text-sm">Dùng lại các file đã upload trước đó (Tiết kiệm thời gian xử lý).</div>
                      </div>
                      <div className="pt-4 border-t border-blue-200">
                        <Text strong>Lưu ý:</Text>
                        <ul className="text-sm text-gray-500 pl-4 list-disc">
                          <li>File PDF nên dưới 20MB.</li>
                          <li>Chủ đề nên liên quan đến nội dung file.</li>
                        </ul>
                      </div>
                  </div>
              </Card>
          </Col>
        </Row>
      </Form>
    </div>
  );
};

export default CreateVideo;