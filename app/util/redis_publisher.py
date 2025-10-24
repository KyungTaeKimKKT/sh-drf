# utils/redis_publisher.py
import redis
import json
import datetime
from django.conf import settings
from typing import List, Dict, Any, Union, Optional

from django.core.cache import cache

class RedisPublisher:
    """
    Redis를 통해 메시지를 발행하는 클래스
    """
    
    def __init__(self, redis_host=None, redis_port=None, redis_db=0, redis_password=None):
        """
        Redis 연결 초기화
        
        Args:
            redis_host: Redis 호스트 (기본값: settings.REDIS_HOST)
            redis_port: Redis 포트 (기본값: settings.REDIS_PORT)
            redis_db: Redis DB 번호 (기본값: 0)
        """
        self.redis_host = redis_host or settings.REDIS_HOST
        self.redis_port = int(redis_port or settings.REDIS_PORT)
        self.redis_db = redis_db
        
        # Redis 클라이언트 초기화
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=redis_password or settings.REDIS_PASSWORD
        )
    
    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """
        지정된 채널에 메시지 발행
        
        Args:
            channel: 메시지를 발행할 채널 이름
            message: 발행할 메시지 데이터 (딕셔너리)
            
        Returns:
            구독자 수
        """
        try:
            # 메시지를 JSON 문자열로 직렬화
            message_str = json.dumps(message, ensure_ascii=False)
            cache.set(f"{channel}:latest", message_str, timeout=60*60)
            
            # 메시지 발행
            subscribers = self.redis_client.publish(channel, message_str)
            return subscribers
        except Exception as e:
            print(f"메시지 발행 중 오류 발생: {e}")
            return 0
    
    def publish_message(self, 
                        channel: str,
                        main_type: str,
                        sub_type: str,
                        action: str,
                        message: str,
                        subject: str = "",
                        receiver: List[str] = ["ALL"],
                        sender: List[int] = [0],
                        extra_data: Optional[Dict[str, Any]] = None) -> int:
        """
        표준 형식의 메시지 발행
        
        Args:
            channel: 메시지를 발행할 채널 이름
            main_type: 메시지 주요 유형 (예: 'message', 'notification')
            sub_type: 메시지 하위 유형 (예: '공지사항', '알림')
            action: 메시지 액션 (예: 'test', 'update')
            message: 메시지 내용
            subject: 메시지 제목 (기본값: "")
            receiver: 수신자 목록 (기본값: ["ALL"])
            sender: 발신자 ID 목록 (기본값: [0])
            extra_data: 추가 데이터 (기본값: None)
            
        Returns:
            구독자 수
        """
        # 기본 메시지 구조 생성
        msg = {
            "main_type": main_type,
            "sub_type": sub_type,
            "action": action,
            "receiver": receiver,
            "subject": subject,
            "message": message,
            "sender": sender,
            "send_time": datetime.datetime.now().isoformat()
        }
        
        # 추가 데이터가 있으면 병합
        if extra_data:
            msg.update(extra_data)
        
        # 메시지 발행
        return self.publish(channel, msg)
    
    def publish_to_multiple_channels(self, 
                                    channels: List[str], 
                                    message: Dict[str, Any]) -> Dict[str, int]:
        """
        여러 채널에 동일한 메시지 발행
        
        Args:
            channels: 메시지를 발행할 채널 이름 목록
            message: 발행할 메시지 데이터 (딕셔너리)
            
        Returns:
            채널별 구독자 수를 담은 딕셔너리
        """
        results = {}
        for channel in channels:
            results[channel] = self.publish(channel, message)
        return results
    
    def publish_notification(self, 
                            channel: str,
                            message: str,
                            subject: str = "알림",
                            receiver: List[str] = ["ALL"],
                            level: str = "info") -> int:
        """
        알림 메시지 발행
        
        Args:
            channel: 메시지를 발행할 채널 이름
            message: 알림 내용
            subject: 알림 제목 (기본값: "알림")
            receiver: 수신자 목록 (기본값: ["ALL"])
            level: 알림 레벨 (기본값: "info", 옵션: "info", "warning", "error")
            
        Returns:
            구독자 수
        """
        return self.publish_message(
            channel=channel,
            main_type="notification",
            sub_type=level,
            action="notify",
            message=message,
            subject=subject,
            receiver=receiver,
            extra_data={"level": level}
        )
    
    def publish_data_update(self, 
                           channel: str,
                           data: Dict[str, Any],
                           data_type: str,
                           action: str = "update",
                           message: str = "",
                           receiver: List[str] = ["ALL"]) -> int:
        """
        데이터 업데이트 메시지 발행
        
        Args:
            channel: 메시지를 발행할 채널 이름
            data: 업데이트된 데이터
            data_type: 데이터 유형 (예: "sensor_data", "user_info")
            action: 데이터 액션 (기본값: "update")
            message: 추가 메시지 (기본값: "")
            receiver: 수신자 목록 (기본값: ["ALL"])
            
        Returns:
            구독자 수
        """
        return self.publish_message(
            channel=channel,
            main_type="data_update",
            sub_type=data_type,
            action=action,
            message=message,
            subject=f"{data_type} 업데이트",
            receiver=receiver,
            extra_data={"data": data}
        )
    
    def close(self):
        """Redis 연결 종료"""
        self.redis_client.close()