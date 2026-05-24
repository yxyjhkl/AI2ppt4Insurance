"""测试进度推送功能"""
import asyncio
import websockets
import json
import time

async def send_test_progress(task_id: str):
    """模拟发送进度更新"""
    uri = f"ws://localhost:8000/api/v1/ws/progress/{task_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ 连接到 WebSocket: {uri}")
            
            # 模拟进度更新
            stages = [
                {"step": 0, "total": 100, "percentage": 0, "stage": "初始化", "message": "开始生成演示文稿"},
                {"step": 10, "total": 100, "percentage": 10, "stage": "内容规划", "message": "分析输入内容并规划幻灯片结构"},
                {"step": 20, "total": 100, "percentage": 20, "stage": "AI 生成", "message": "正在调用 AI 生成内容..."},
                {"step": 40, "total": 100, "percentage": 40, "stage": "AI 生成", "message": "AI 正在分析内容结构"},
                {"step": 60, "total": 100, "percentage": 60, "stage": "AI 生成", "message": "AI 生成完成"},
                {"step": 70, "total": 100, "percentage": 70, "stage": "渲染幻灯片", "message": "正在渲染 SVG 预览..."},
                {"step": 85, "total": 100, "percentage": 85, "stage": "生成 PPTX", "message": "正在组装 PPTX 文件..."},
                {"step": 95, "total": 100, "percentage": 95, "stage": "质量检查", "message": "正在进行质量检查..."},
                {"step": 100, "total": 100, "percentage": 100, "stage": "完成", "message": "生成完成"},
            ]
            
            for progress in stages:
                message = json.dumps({"type": "progress", **progress})
                await websocket.send(message)
                print(f"📤 发送进度: {progress['stage']} ({progress['percentage']}%)")
                time.sleep(1)  # 等待1秒
            
            print("🎉 测试完成！")
            
    except websockets.exceptions.ConnectionRefusedError:
        print("❌ 无法连接到 WebSocket 服务器，请确保后端服务已启动")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    # 使用模拟的 task_id
    test_task_id = "task_test1234"
    print(f"🚀 开始测试进度推送，task_id: {test_task_id}")
    print("提示：请先启动后端服务，然后在前端使用此 task_id 连接")
    print()
    
    asyncio.run(send_test_progress(test_task_id))
