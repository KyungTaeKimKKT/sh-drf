import logging
from django.conf import settings
import util.utils_func as utils

class WebSocketMessageSender:
    """
    웹소켓 메시지 전송을 위한 클래스
    
    사용 예시:
    ```
    # 기본 사용법
    WebSocketMessageSender(obj).subject("제목").message("내용").progress(50).send()
    
    # 체이닝 사용법
    WebSocketMessageSender(obj).subject("제목").message("내용").progress(50).receiver([1, 2]).send()
    
    # URL 지정
    WebSocketMessageSender(obj, url=settings.WS_URL_특정).subject("제목").message("내용").send()
    ```
    """
    
    def __init__(self, obj=None, url=None, **kwargs):
        """
        웹소켓 메시지 전송 클래스 초기화
        
        Args:
            obj: 메시지와 관련된 객체 (선택적)
            url: 웹소켓 URL (선택적)
            **kwargs: 추가 키워드 인수 (선택적)
        """
        self.obj = obj
        self.url = url or getattr(settings, 'WS_URL_DEFAULT', 'ws://localhost:8000/ws/notifications/')
        self.logger = logging.getLogger(__name__)

        self.kwargs = kwargs
        self.receiver = self.kwargs.get('receiver', [])
        self.sender = self.kwargs.get('sender', 1)
        
        # 기본 메시지 구조 초기화
        self.msg = {
            'main_type': 'notice',
            'sub_type': '알림',
            'receiver': self.receiver,
            'subject': '',
            'message': '',
            'sender': self.sender,
            'progress': 0,
        }
        
        # 객체에서 receiver 정보 추출 (가능한 경우)
        if obj and hasattr(obj, '등록자_fk') and obj.등록자_fk:
            self.msg['receiver'] = [obj.등록자_fk.id]
    
    def subject(self, subject):
        """제목 설정"""
        self.msg['subject'] = subject
        return self
    
    def sub_subject(self, sub_subject):
        """서브 제목 설정"""
        self.msg['sub_subject'] = sub_subject
        return self
    
    def message(self, message):
        """메시지 내용 설정"""
        self.msg['message'] = message
        return self
    
    def progress(self, progress):
        """진행률 설정 (0-100)"""
        self.msg['progress'] = progress
        return self
    
    def receiver(self, receiver_ids):
        """수신자 ID 설정"""
        if isinstance(receiver_ids, list):
            self.msg['receiver'] = receiver_ids
        else:
            self.msg['receiver'] = [receiver_ids]
        return self
    
    def sender(self, sender_id):
        """발신자 ID 설정"""
        self.msg['sender'] = sender_id
        return self
    
    def main_type(self, main_type):
        """메인 타입 설정"""
        self.msg['main_type'] = main_type
        return self
    
    def sub_type(self, sub_type):
        """서브 타입 설정"""
        self.msg['sub_type'] = sub_type
        return self
    
    def set_url(self, url):
        """웹소켓 URL 설정"""
        self.url = url
        return self
    
    def custom(self, key, value):
        """사용자 정의 속성 설정"""
        self.msg[key] = value
        return self
    
    def send(self):
        """메시지 전송"""
        try:
            utils.send_WS_msg_short(self.obj, url=self.url, msg=self.msg)
            return True
        except Exception as e:
            self.logger.error(f"웹소켓 메시지 전송 중 오류 발생: {str(e)}")
            return False
        
    def file(self, filename, file_content):
        """
        파일 첨부 설정
        
        Args:
            filename: 파일 이름
            file_content: 파일 내용 (바이트)
        """
        import base64
        
        # 파일 내용을 base64로 인코딩
        if isinstance(file_content, bytes):
            encoded_content = base64.b64encode(file_content).decode('utf-8')
        else:
            # 문자열인 경우 바이트로 변환 후 인코딩
            encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
        
        # 파일 정보 설정
        self.msg['file'] = {
            'filename': filename,
            'content': encoded_content,
            'content_type': self._get_content_type(filename)
        }
        return self
    
    def _get_content_type(self, filename):
        """파일 확장자에 따른 MIME 타입 반환"""
        import mimetypes
        
        # 기본 MIME 타입 매핑 확장
        if not mimetypes.inited:
            mimetypes.init()
            mimetypes.add_type('text/csv', '.csv')
            mimetypes.add_type('application/vnd.ms-excel', '.xls')
            mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')
        
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    @classmethod
    def quick_send(cls, obj=None, url=None, **kwargs):
        """
        빠른 메시지 전송을 위한 클래스 메서드
        
        Args:
            obj: 메시지와 관련된 객체 (선택적)
            url: 웹소켓 URL (선택적)
            **kwargs: 메시지 속성 (subject, message, progress 등)
            
        Returns:
            bool: 메시지 전송 성공 여부
        """
        sender = cls(obj, url)
        
        for key, value in kwargs.items():
            if hasattr(sender, key) and callable(getattr(sender, key)):
                # 메서드가 있으면 호출
                getattr(sender, key)(value)
            else:
                # 없으면 custom 메서드로 설정
                sender.custom(key, value)
        
        return sender.send()