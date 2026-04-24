import requests
import json
from typing import Dict

class WeChatNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_alert(self, alert: Dict):
        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"""
**【告警通知】**

**告警名称**: {alert.get('labels', {}).get('alertname', 'Unknown')}
**级别**: {alert.get('labels', {}).get('severity', 'P2')}
**摘要**: {alert.get('annotations', {}).get('summary', '')}
**详情**: {alert.get('annotations', {}).get('description', '')}
**时间**: {alert.get('startsAt', '')}
"""
            }
        }
        
        try:
            response = requests.post(self.webhook_url, json=message)
            return response.status_code == 200
        except Exception as e:
            print(f"WeChat notification failed: {e}")
            return False

class DingTalkNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_alert(self, alert: Dict):
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"告警: {alert.get('labels', {}).get('alertname', 'Unknown')}",
                "text": f"""
### 告警通知

**告警名称**: {alert.get('labels', {}).get('alertname', 'Unknown')}
**级别**: {alert.get('labels', {}).get('severity', 'P2')}
**摘要**: {alert.get('annotations', {}).get('summary', '')}
**详情**: {alert.get('annotations', {}).get('description', '')}
"""
            }
        }
        
        try:
            response = requests.post(self.webhook_url, json=message)
            return response.status_code == 200
        except Exception as e:
            print(f"DingTalk notification failed: {e}")
            return False

def alert_webhook_handler(alert_data: Dict):
    alerts = alert_data.get("alerts", [])
    
    for alert in alerts:
        severity = alert.get("labels", {}).get("severity", "P2")
        
        if severity == "P0":
            wechat = WeChatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
            dingtalk = DingTalkNotifier("https://oapi.dingtalk.com/robot/send?access_token=xxx")
            wechat.send_alert(alert)
            dingtalk.send_alert(alert)
        elif severity == "P1":
            wechat = WeChatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
            wechat.send_alert(alert)
        elif severity == "P2":
            print(f"P2 Alert: {alert.get('labels', {}).get('alertname')}")