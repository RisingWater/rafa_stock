import React from 'react';
import { Input, Button, Card, Space, DatePicker, Form, Row, Col } from 'antd';
import { SearchOutlined, CalendarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const StockSearch = ({ onStockSelect, loading }) => {
  const [form] = Form.useForm();
  const [selectedDate, setSelectedDate] = React.useState(dayjs());

  const handleSearch = (values) => {
    const { stockCode, endDate } = values;
    if (!stockCode?.trim()) {
      message.warning('请输入股票代码');
      return;
    }
    
    const dateParam = endDate ? endDate.format('YYYY-MM-DD') : null;
    onStockSelect(stockCode.trim(), dateParam);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      form.submit();
    }
  };

  return (
    <Card title="股票查询" style={{ marginBottom: 24 }}>
      <Form
        form={form}
        onFinish={handleSearch}
        initialValues={{
          stockCode: '002363',
          endDate: dayjs()
        }}
      >
        <Row gutter={16} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Form.Item
              name="stockCode"
              rules={[{ required: true, message: '请输入股票代码' }]}
            >
              <Input
                placeholder="输入股票代码，如：000001"
                onKeyPress={handleKeyPress}
                size="large"
                prefix={<SearchOutlined />}
              />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <Form.Item name="endDate">
              <DatePicker
                placeholder="选择结束日期"
                size="large"
                style={{ width: '100%' }}
                format="YYYY-MM-DD"
                disabledDate={(current) => {
                  return current && current > dayjs().endOf('day');
                }}
                suffixIcon={<CalendarOutlined />}
              />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={24} md={8}>
            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={loading}
                size="large"
                style={{ width: '100%' }}
              >
                查询
              </Button>
            </Form.Item>
          </Col>
        </Row>
        
        <div style={{ marginTop: 8, color: '#666', fontSize: '12px' }}>
          提示：不选择日期则默认查询最新数据
        </div>
      </Form>
    </Card>
  );
};

export default StockSearch;