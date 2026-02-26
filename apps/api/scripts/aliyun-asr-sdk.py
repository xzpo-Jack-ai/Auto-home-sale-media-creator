#!/usr/bin/env python3
"""
阿里云 ASR 转写 - 使用阿里云 Python SDK

安装:
    pip3 install alibabacloud-nls-java-sdk --break-system-packages
    或
    pip3 install aliyun-python-sdk-core aliyun-python-sdk-nls --break-system-packages

配置环境变量:
    export ALIYUN_ACCESS_KEY_ID=your_access_key_id
    export ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
    export ALIYUN_APP_KEY=your_app_key
"""

import os
import sys
import json
import time

def transcribe_file(file_url: str) -> dict:
    """
    使用阿里云录音文件识别转写音频
    
    Args:
        file_url: 音频文件URL（需要阿里云可访问）
    
    Returns:
        dict: {success, transcript, duration, cost, error}
    """
    
    # 获取配置
    access_key_id = os.environ.get('ALIYUN_ACCESS_KEY_ID')
    access_key_secret = os.environ.get('ALIYUN_ACCESS_KEY_SECRET')
    app_key = os.environ.get('ALIYUN_APP_KEY')
    
    if not all([access_key_id, access_key_secret, app_key]):
        return {
            'success': False,
            'error': '阿里云配置不完整。请设置环境变量: ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_APP_KEY'
        }
    
    try:
        # 尝试导入阿里云 SDK
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.request import CommonRequest
        
        # 创建客户端
        client = AcsClient(access_key_id, access_key_secret, 'cn-shanghai')
        
        # 提交任务
        print(f"🚀 提交转写任务...")
        
        submit_request = CommonRequest()
        submit_request.set_accept_format('json')
        submit_request.set_domain('filetrans.cn-shanghai.aliyuncs.com')
        submit_request.set_method('POST')
        submit_request.set_protocol_type('https')
        submit_request.set_version('2022-12-14')
        submit_request.set_action_name('SubmitTask')
        
        submit_request.add_query_param('appkey', app_key)
        submit_request.add_query_param('fileLink', file_url)
        
        # 可选参数
        submit_request.add_query_param('enableInverseTextNormalization', 'true')
        submit_request.add_query_param('enablePunctuation', 'true')
        
        submit_response = client.do_action_with_exception(submit_request)
        submit_result = json.loads(submit_response)
        
        if submit_result.get('StatusCode') != 21050000:
            return {
                'success': False,
                'error': f"提交任务失败: {submit_result.get('StatusText', '未知错误')}"
            }
        
        task_id = submit_result['TaskId']
        print(f"✅ 任务已提交: {task_id}")
        
        # 轮询查询结果
        print(f"⏳ 等待转写完成...")
        max_wait = 60  # 最多等待60秒
        poll_interval = 2
        
        for i in range(0, max_wait, poll_interval):
            time.sleep(poll_interval)
            
            query_request = CommonRequest()
            query_request.set_accept_format('json')
            query_request.set_domain('filetrans.cn-shanghai.aliyuncs.com')
            query_request.set_method('GET')
            query_request.set_protocol_type('https')
            query_request.set_version('2022-12-14')
            query_request.set_action_name('GetTaskResult')
            
            query_request.add_query_param('appkey', app_key)
            query_request.add_query_param('taskId', task_id)
            
            query_response = client.do_action_with_exception(query_request)
            query_result = json.loads(query_response)
            
            status_code = query_result.get('StatusCode')
            
            if status_code == 21050000:
                # 成功
                result_data = query_result.get('Result', {})
                sentences = result_data.get('Sentences', [])
                transcript = ''.join([s.get('Text', '') for s in sentences])
                duration = result_data.get('AudioDuration', 0)
                
                # 计算费用 (¥2.5/小时)
                cost = round(max(15, duration / 1000) / 3600 * 2.5, 4)
                
                return {
                    'success': True,
                    'transcript': transcript,
                    'duration': duration,
                    'cost': cost
                }
            
            elif status_code == 21050001:
                # 处理中
                print(f"   处理中... ({i+poll_interval}s)")
                continue
            
            else:
                # 失败
                return {
                    'success': False,
                    'error': f"转写失败: {query_result.get('StatusText', '未知错误')}"
                }
        
        return {
            'success': False,
            'error': '转写超时'
        }
        
    except ImportError:
        return {
            'success': False,
            'error': '阿里云 SDK 未安装。请运行: pip3 install aliyun-python-sdk-core --break-system-packages'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'转写异常: {str(e)}'
        }


def main():
    """测试脚本"""
    file_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not file_url:
        print("用法: python3 aliyun-asr-sdk.py <音频URL>")
        print("\n请配置环境变量:")
        print("  export ALIYUN_ACCESS_KEY_ID=your_access_key_id")
        print("  export ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret")
        print("  export ALIYUN_APP_KEY=your_app_key")
        sys.exit(1)
    
    result = transcribe_file(file_url)
    
    print("\n" + "="*50)
    if result['success']:
        print(f"✅ 转写成功")
        print(f"时长: {result['duration']}ms")
        print(f"费用: ¥{result['cost']}")
        print(f"\n转写结果:\n{result['transcript'][:500]}...")
    else:
        print(f"❌ 转写失败: {result['error']}")
    
    print("\n===JSON_START===")
    print(json.dumps(result, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == '__main__':
    main()
