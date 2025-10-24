from django.db import models
import uuid
import os
import json, requests
from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re


def csv_file_path(instance, filename):
    """Generate file path for new recipe image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'elevator', filename)


class Elevator_시도_시군구(models.Model):
    시도 = models.CharField(max_length=20)
    시군구 = models.CharField(max_length=30)
    수량 = models.IntegerField(default=0)


#  google region chart를 이용할려면,
#  ISO3166:KR의 Local Variant를 이용해야 한다.
#  name_en field에 기입
class ISO3166_KR(models.Model):
    code = models.CharField(max_length=10)
    name_en = models.CharField(max_length=30)
    name_kor = models.CharField(max_length=30)
    name_for_elevator = models.CharField(max_length=30)
    지사 = models.CharField(max_length=30,blank=True)

    def __str__(self):
        return self.name_en

class Elevator(models.Model):
    """ Elevator Model"""
    건물명 =  models.CharField(max_length=100)
    건물주소 =  models.CharField(max_length=254)
    건물주소_찾기용 =  models.CharField(max_length=254, null=True, blank=True)
    loc_x = models.FloatField()
    loc_y = models.FloatField()
    시도 = models.CharField(max_length=20)
    시도_ISO = models.ForeignKey( ISO3166_KR, on_delete = models.CASCADE ,null=True )
    시군구 = models.CharField(max_length=30)
    승강기고유번호 = models.CharField(max_length=20)
    검사유효만료일자 = models.DateField(null=True, blank=True)
    승강기구분 = models.CharField(max_length=30, null=True,blank=True)
    승강기형식 = models.CharField(max_length=20, null=True,blank=True)
    승강기세부형식 = models.CharField(max_length=20, null=True,blank=True)
    승강기종류 = models.CharField(max_length=30, null=True,blank=True)
    운행층수 = models.IntegerField()
    주행길이 = models.CharField(max_length=10, null=True, blank=True)
    정격속도 = models.CharField(max_length=10, null=True, blank=True)
    적재하중 = models.CharField(max_length=10, null=True, blank=True)
    최대정원 =models.CharField(max_length=10, null=True, blank=True)
    제조업체 = models.CharField(max_length=30)
    유지관리업체 = models.CharField(max_length=30)
    운행지상층수 = models.CharField(max_length=10, null=True, blank=True)
    운행지하층수 = models.CharField(max_length=10, null=True, blank=True)
    건물용도_대 = models.CharField(max_length=30)
    건물용도_소 = models.CharField(max_length=50)
    기계실유무 = models.BooleanField()
    최초설치일자 = models.DateField()
    설치일자 = models.DateField()
    승강기상태 = models.CharField(max_length=20)
    검사결과이력조회코드 = models.CharField(max_length=20)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.건물명
    
    def save(self, *args, **kwargs):
        if self.loc_x is None:
            self.건물주소_찾기용 = self.get_주소찾기용주소(self.건물주소)
            # self.시도_ISO = ISO3166_KR.objects.get(name_for_elevator = self.시도)
            self.기계실유무 = True if 'Y' in str(self.기계실유무) else False
            self.검사유효만료일자 = datetime.strptime(self.검사유효만료일자,"%Y-%m-%d").date() if ( len(str(self.검사유효만료일자)) >= 10 ) else None
            self.최초설치일자 = datetime.strptime(self.최초설치일자,"%Y-%m-%d").date() if ( len(str(self.최초설치일자)) >= 10 ) else None
            self.설치일자 = datetime.strptime(self.설치일자,"%Y-%m-%d").date() if ( len(str(self.설치일자)) >= 10 ) else None
            self.운행층수 = int(self.운행층수)  if self.운행층수 != None else 0        

            self.loc_x = 0
            self.loc_y = 0
            # if ( (obj:=self.getOjbectOrNone() ) == None ) :
            #     (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
            # else:
            #     (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )
            super(Elevator, self).save(*args, **kwargs)

        elif ( self.loc_x >0 and self.loc_y > 0) :
            super(Elevator, self).save(*args, **kwargs)
        else :
            if (self.id > 0 ):
                if ( (obj:=self.getOjbectOrNone() ) == None ) :
                    (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
                else:
                    (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )
            else : 
                self.기계실유무 = True if 'Y' in self.기계실유무 else False
                if ( len(str(self.검사유효만료일자)) >= 10 ) :
                    self.검사유효만료일자= datetime.strptime(self.검사유효만료일자,"%Y-%m-%d").date()
                else : self.검사유효만료일자 = None
                self.최초설치일자= datetime.strptime(self.최초설치일자,"%Y-%m-%d").date()
                self.설치일자= datetime.strptime(self.설치일자,"%Y-%m-%d").date()       
                self.운행층수 = int(self.운행층수)  if self.운행층수 != None else 0

                self.loc_x = 0
                self.loc_y = 0
                # if ( (obj:=self.getOjbectOrNone() ) == None ) :
                #     (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
                # else:
                #     (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )

            super(Elevator, self).save(*args, **kwargs)

    def get_주소찾기용주소(self, 주소):
        pattern1 = re.compile(r"\((.*?)\)")
        pattern2 = re.compile(r"\외(.*?)\필지")
        주소 = pattern1.sub("",주소)
        주소 = pattern2.sub("",주소)
        return 주소

    def get_location(self, address):
        url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
        headers = {"Authorization": "KakaoAK 61d575c9329b41b9c6647a006939454e"}
        api_json = json.loads(str(requests.get(url,headers=headers).text))

        api_address_li = api_json['documents']
        
        
        if len( api_address_li ) == 0 :
            return (0,0)  
        else :
            if "address" in api_address_li[0] and api_address_li[0]['address'] is not None:
                address = api_json['documents'][0]['address'] 

            elif "road_address" in api_address_li[0] and api_address_li[0]['address']  is not None :
                address = api_json['documents'][0]['road_address'] 

            else : return (0,0)

            return (address['x'], address['y'])
    
    def getOjbectOrNone(self):
        try:
            return Elevator.objects.get(건물명=self.건물명, 건물주소=self.건물주소)
        except Elevator.DoesNotExist:
            return None
        except Elevator.MultipleObjectsReturned:
            return Elevator.objects.filter(건물명=self.건물명, 건물주소=self.건물주소).order_by('id')[0]


class Csvupload(models.Model):
    csv = models.FileField(null=True, upload_to=csv_file_path)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.csv
    
    def save(self, *args, **kwargs):
        super(Csvupload, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.csv.delete()
        super(Csvupload, self).delete(*args, **kwargs)

class Elevator_Summary(models.Model):
    """ Elevator Model"""
    건물명 =  models.CharField(max_length=100)
    건물주소 =  models.CharField(max_length=254)
    건물주소_찾기용 =  models.CharField(max_length=254, null=True, blank=True)
    loc_x = models.FloatField()
    loc_y = models.FloatField()
    시도 = models.CharField(max_length=20)
    시도_ISO = models.ForeignKey( ISO3166_KR, on_delete = models.CASCADE ,null=True )
    시군구 = models.CharField(max_length=30)
    최초설치일자 = models.DateField()

    수량 = models.IntegerField(default=0)
    해당_els = models.ManyToManyField(Elevator)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.건물명
    
    def save(self, *args, **kwargs):
        if self.loc_x is None:
            self.건물주소_찾기용 = self.get_주소찾기용주소(self.건물주소)
            self.시도_ISO = ISO3166_KR.objects.get(name_for_elevator = self.시도)
            self.loc_x = 0
            self.loc_y = 0
            # if ( (obj:=self.getOjbectOrNone() ) == None ) :
            #     (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
            # else:
            #     (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )
            super(Elevator_Summary, self).save(*args, **kwargs)

# https://stackoverflow.com/questions/58254104/how-can-i-access-a-manytomanyfield-in-the-save-method-of-a-model
            qs = Elevator.objects.filter( 건물명=self.건물명, 건물주소=self.건물주소, 최초설치일자=self.최초설치일자)
            if ( self.수량 ==  qs.count() ):
                for _instance in qs:
                    self.해당_els.add(_instance )

        elif ( self.loc_x >0 and self.loc_y > 0) :
            super(Elevator, self).save(*args, **kwargs)
        else :
            if (self.id > 0 ):
                if ( (obj:=self.getOjbectOrNone() ) == None ) :
                    (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
                else:
                    (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )
            else : 
                self.기계실유무 = True if 'Y' in self.기계실유무 else False
                if ( len(str(self.검사유효만료일자)) >= 10 ) :
                    self.검사유효만료일자= datetime.strptime(self.검사유효만료일자,"%Y-%m-%d").date()
                else : self.검사유효만료일자 = None
                self.최초설치일자= datetime.strptime(self.최초설치일자,"%Y-%m-%d").date()
                self.설치일자= datetime.strptime(self.설치일자,"%Y-%m-%d").date()       
                self.운행층수 = int(self.운행층수)  if self.운행층수 != None else 0

                self.loc_x = 0
                self.loc_y = 0
                # if ( (obj:=self.getOjbectOrNone() ) == None ) :
                #     (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
                # else:
                #     (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )

            super(Elevator, self).save(*args, **kwargs)

    def get_주소찾기용주소(self, 주소):
        pattern1 = re.compile(r"\((.*?)\)")
        pattern2 = re.compile(r"\외(.*?)\필지")
        주소 = pattern1.sub("",주소)
        주소 = pattern2.sub("",주소)
        return 주소

    def get_location(self, address):
        url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
        headers = {"Authorization": "KakaoAK 61d575c9329b41b9c6647a006939454e"}
        api_json = json.loads(str(requests.get(url,headers=headers).text))

        api_address_li = api_json['documents']
        
        
        if len( api_address_li ) == 0 :
            return (0,0)  
        else :
            if "address" in api_address_li[0] and api_address_li[0]['address'] is not None:
                address = api_json['documents'][0]['address'] 

            elif "road_address" in api_address_li[0] and api_address_li[0]['address']  is not None :
                address = api_json['documents'][0]['road_address'] 

            else : return (0,0)

            return (address['x'], address['y'])
    
    def getOjbectOrNone(self):
        try:
            return Elevator.objects.get(건물명=self.건물명, 건물주소=self.건물주소)
        except Elevator.DoesNotExist:
            return None
        except Elevator.MultipleObjectsReturned:
            return Elevator.objects.filter(건물명=self.건물명, 건물주소=self.건물주소).order_by('id')[0]


class Elevator_Summary_WO설치일(models.Model):
    """ Elevator Model 설치일을 가장 빠른 1개로"""
    건물명 =  models.CharField(max_length=100)
    건물주소 =  models.CharField(max_length=254)
    건물주소_찾기용 =  models.CharField(max_length=254, null=True, blank=True)
    loc_x = models.FloatField()
    loc_y = models.FloatField()
    시도 = models.CharField(max_length=20)
    시도_ISO = models.ForeignKey( ISO3166_KR, on_delete = models.CASCADE ,null=True )
    시군구 = models.CharField(max_length=30)
    최초설치일자 = models.DateField()

    수량 = models.IntegerField(default=0)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.건물명
    
    def save(self, *args, **kwargs):
        if self.loc_x is None:
            # self.건물주소_찾기용 = self.get_주소찾기용주소(self.건물주소)
            self.시도_ISO = ISO3166_KR.objects.get(name_for_elevator = self.시도)
            self.loc_x = 0
            self.loc_y = 0
            # self.최초설치일자 = Elevator_Summary.objects.filter(건물명=self.건물명, 건물주소=self.건물주소).order_by('최초설치일자')[0].최초설치일자
            # if ( (obj:=self.getOjbectOrNone() ) == None ) :
            #     (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
            # else:
            #     (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )
            super(Elevator_Summary_WO설치일, self).save(*args, **kwargs)

    def get_운행층수(self):
        _search_dict = {
            '건물명':self.건물명,
            '건물주소':self.건물주소,
        }
        qs = Elevator.objects.filter(**_search_dict)
        return qs.aggregate(models.Sum('운행층수'))['운행층수__sum'] or 0
        # elif ( self.loc_x >0 and self.loc_y > 0) :
        #     super(Elevator_Summary_WO설치일, self).save(*args, **kwargs)
        # else :
        #     if (self.id > 0 ):
        #         if ( (obj:=self.getOjbectOrNone() ) == None ) :
        #             (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
        #         else:
        #             (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )
        #     else : 
        #         self.기계실유무 = True if 'Y' in self.기계실유무 else False
        #         if ( len(str(self.검사유효만료일자)) >= 10 ) :
        #             self.검사유효만료일자= datetime.strptime(self.검사유효만료일자,"%Y-%m-%d").date()
        #         else : self.검사유효만료일자 = None
        #         self.최초설치일자= datetime.strptime(self.최초설치일자,"%Y-%m-%d").date()
        #         self.설치일자= datetime.strptime(self.설치일자,"%Y-%m-%d").date()       
        #         self.운행층수 = int(self.운행층수)  if self.운행층수 != None else 0

        #         self.loc_x = 0
        #         self.loc_y = 0
        #         # if ( (obj:=self.getOjbectOrNone() ) == None ) :
        #         #     (self.loc_x,  self.loc_y ) = self.get_location(self.건물주소)
        #         # else:
        #         #     (self.loc_x,  self.loc_y ) = ( obj.loc_x,  obj.loc_y )

        #     super(Elevator_Summary_WO설치일, self).save(*args, **kwargs)

    def get_주소찾기용주소(self, 주소):
        pattern1 = re.compile(r"\((.*?)\)")
        pattern2 = re.compile(r"\외(.*?)\필지")
        주소 = pattern1.sub("",주소)
        주소 = pattern2.sub("",주소)
        return 주소

    def get_location(self, address):
        url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
        headers = {"Authorization": "KakaoAK 61d575c9329b41b9c6647a006939454e"}
        api_json = json.loads(str(requests.get(url,headers=headers).text))

        api_address_li = api_json['documents']
        
        
        if len( api_address_li ) == 0 :
            return (0,0)  
        else :
            if "address" in api_address_li[0] and api_address_li[0]['address'] is not None:
                address = api_json['documents'][0]['address'] 

            elif "road_address" in api_address_li[0] and api_address_li[0]['address']  is not None :
                address = api_json['documents'][0]['road_address'] 

            else : return (0,0)

            return (address['x'], address['y'])
    
    def getOjbectOrNone(self):
        try:
            return Elevator.objects.get(건물명=self.건물명, 건물주소=self.건물주소)
        except Elevator.DoesNotExist:
            return None
        except Elevator.MultipleObjectsReturned:
            return Elevator.objects.filter(건물명=self.건물명, 건물주소=self.건물주소).order_by('id')[0]

