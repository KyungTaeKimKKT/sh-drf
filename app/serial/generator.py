from datetime import datetime

class SerialGenerator:
    @staticmethod
    def generate_serial(공정코드: str, 고객사: str, prefix: str = None) -> str:
        yymmdd = datetime.today().strftime('%y%m%d')
        고객코드 = SerialGenerator._get_고객코드(고객사)
        
        search = f"{공정코드}{yymmdd}{고객코드}"
        serial_num = SerialGenerator._get_next_serial(search)
        
        return f"{공정코드}{yymmdd}{고객코드}-{serial_num}"
    
    @staticmethod
    def _get_고객코드(고객사: str) -> str:
        코드_매핑 = {
            '현대': 'HY',
            'OTIS': 'OT',
            'TKE': 'TK'
        }
        return 코드_매핑.get(고객사, 'ET')
    
    @staticmethod
    def _get_next_serial(search: str) -> str:
        from .models import SerialDB
        qs = SerialDB.objects.filter(serial__icontains=search).order_by('-id')
        if qs:
            latest_serial = int(qs[0].serial.split('-')[-1])
            return str(latest_serial + 1).zfill(5)
        return str(1).zfill(5)