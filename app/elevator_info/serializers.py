"""
Serializers for csv file upload APIs
"""
from django.db.models import Sum
from rest_framework import serializers

from .models import (
    Csvupload, 
    Elevator,
    Elevator_Summary_WO설치일
)
import pandas as pd
from collections import defaultdict

class 승강기협회_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Elevator
        fields = [f.name for f in Elevator._meta.fields] 
        read_only_fields = ['id']



class Elevator_Summary_WO설치일_Serializer(serializers.ModelSerializer):
    운행층수 = serializers.SerializerMethodField('_get_운행층수')

    class Meta:
        model = Elevator_Summary_WO설치일
        fields = [f.name for f in Elevator_Summary_WO설치일._meta.fields] + ['운행층수']
        read_only_fields = ['id']

    def _get_운행층수(self, instance):
        return  Elevator.objects.filter(건물명=instance.건물명, 건물주소=instance.건물주소).aggregate(Sum('운행층수'))['운행층수__sum']
        

class CsvUpload_Serializer(serializers.ModelSerializer):
    """Serializer for Csvuploadupload."""

    class Meta:
        model = Csvupload
        fields = '__all__' 
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a csvupload."""
        file = validated_data['csv']
        # file = serializer.validated_data['csv']
        # https://stackoverflow.com/questions/68426042/how-to-avoid-unnamed-columns-during-read-csv-using-pandas
        types = defaultdict(str,운행층수='int' )
        df = pd.read_csv(file, low_memory=False, dtype='str', converters={'운행층수':int}, #keep_default_na=False,
                     usecols=lambda c: not c.startswith('Unnamed:'))
        qs = Elevator.objects.all()


        error_cnt = 0
        success_cnt = 0
        count = 0
        __dict = df.to_dict('records')
        # for obj in __dict :
        #     if ( count % 1000 == 0):
        #         print (f'{count/qs.count() *100}% 진행 ===> 실패 count {error_cnt} \n\n'  )
        #     # print ( obj )
        #     # print ( 'count : ', count )
        #     count +=1
        #     # if (obj['승강기고유번호'] in df.values  ) : success_cnt +=1
        #     # else: error_cnt +=1
        #     try : 
        #         # print ('success : ', success_cnt)
        #         success_cnt +=1
        #         qs.get( 승강기고유번호=obj['승강기고유번호'] )
        #     except :
        #         # print ('error : ', error_cnt)
        #         error_cnt +=1


        # df = df.astype( {'승강기고유번호': str})
        # print (df )
        

        count = 0; 
        if ( total :=qs.count() ) :
            
            for _obj in qs:
                if '.' in _obj.승강기고유번호:
                    _obj.승강기고유번호 = _obj.승강기고유번호.split('.')[0]
                    _obj.save()
                if ( count % 1000 == 0 ) :
                    print (f'{count/total *100}% 진행  ')
                count +=1
            # df_DB = pd.DataFrame( list(qs.values()) )
            # df_DB = df_DB.drop( columns=['loc_x','loc_y','건물주소_찾기용', '시도_ISO_id', 'timestamp', 'id'] )
            # compare_df = df.iloc[:]
            # # compare_df.drop()
            # # sort by 승강기고유번호
            # df_DB.sort_values('승강기고유번호')
            # compare_df.sort_values('승강기고유번호')


            # print (df_DB)
            # print ( compare_df)
            # result = compare_df.compare(df_DB)
            # print ( result)


            # print (df_DB['승강기고유번호'].isin(df['승강기고유번호']).value_counts()  )
        # else :
        #     count = 0
        #     for dict_data in __dict :
        #         # create instance of model
        #         m = Elevator(**dict_data)
        #         # don't forget to save to database!
        #         m.save()
        #         print ( count, '/ ', len(__dict) )
        #         count +=1

        # csvupload = Csvupload.objects.create(**validated_data)
        # return csvupload
    
