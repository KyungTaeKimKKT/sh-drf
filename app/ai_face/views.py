from __future__ import annotations
from re import sub

from pandas.core.computation.ops import isnumeric
from shapi.view_common_import import *
from . import models, serializers
from util.base_model_viewset import BaseModelViewSet


from users.models import User

import ai_face.app_util as App_util

import numpy as np

REDIS_CHANNEL_REQUEST =  "broadcast:request_analyze" ### 받는 곳은  SUB 임.
REDIS_CHANNEL_RESPONSE =  "broadcast:response_analyze" ### 보내는 곳은  PUB 임.

RPC_REGISTER_HOST = os.getenv("RPC_REGISTER_HOST", "192.168.10.249")
RPC_REGISTER_PORT = int(os.getenv("RPC_REGISTER_PORT", 50051))
RPC_REGISTER_ADDRESS = f"{RPC_REGISTER_HOST}:{RPC_REGISTER_PORT}"

RPC_RECOGNIZE_HOST = os.getenv("RPC_RECOGNIZE_HOST", "192.168.10.249")
RPC_RECOGNIZE_PORT = int(os.getenv("RPC_RECOGNIZE_PORT", 50052))
RPC_RECOGNIZE_ADDRESS = f"{RPC_RECOGNIZE_HOST}:{RPC_RECOGNIZE_PORT}"

MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL
SAVE_ROOT = "tmp/ai_face"
MEDIA_TMP_DIR = os.path.join(MEDIA_ROOT, SAVE_ROOT)
os.makedirs(MEDIA_TMP_DIR, exist_ok=True)


import grpc
from ai_face.grpc import face_register_pb2_grpc, face_register_pb2, face_recognize_pb2_grpc, face_recognize_pb2
from google.protobuf.json_format import MessageToDict

def register_face_via_grpc(request_data: dict):
    with grpc.insecure_channel(RPC_REGISTER_ADDRESS) as channel:
        stub = face_register_pb2_grpc.FaceRegisterServiceStub(channel)
        print ("rpc request_data:", request_data)
        extra_path_messages = [
            face_register_pb2.ExtraPath(id=fi["id"], path=fi["path"])
            for fi in request_data["extra_paths"]
        ]
        response = stub.RegisterFace(face_register_pb2.FaceRegisterRequest( 
            id=request_data["id"],
            user_id=request_data["user_id"],
            image_path=request_data["image_path"],
            extra_paths=extra_path_messages
            ))
        print( "rpc response:", type(response), response)
        return response

def recognize_face_via_grpc(request_data: dict):
    with grpc.insecure_channel(RPC_RECOGNIZE_ADDRESS) as channel:
        stub = face_recognize_pb2_grpc.FaceServiceStub(channel)
        print ("rpc request_data:", "image_paths:", request_data["image_paths"], "ws_url:", request_data["ws_url"])
        response = stub.RecognizeFace(face_recognize_pb2.FaceRequest( 
            image_paths=request_data["image_paths"],
            ws_url=request_data["ws_url"]
            ))
        print( "rpc response:", type(response), response)
        return response




class UserFaceViewSet(viewsets.ModelViewSet):   
    MODEL = models.UserFace
    queryset = models.UserFace.objects.all()
    serializer_class = serializers.UserFaceSerializer

    redis_publisher = RedisPublisher()

    @action(detail=False, methods=["get"], url_path="list_user_to_face", permission_classes=[IsAuthenticated])
    def list_user_to_face(self, request):
        """
        사용자 목록 조회 : query params 사용
        - is_active: True/False
        - user_id: 사용자 ID (all: 전체, 숫자: 특정 사용자)
        """
        ### query params parsing
        is_active = request.query_params.get("is_active", "True")
        is_active = bool( is_active.lower() in ["true", "1", "yes", "y"])
        user_id = request.query_params.get("user_id", "all")

        filter_kwargs = {"is_active": is_active}
        if user_id != "all" and str(user_id).isnumeric() and int(user_id) > 0:
            filter_kwargs["id"] = int(user_id)

        users = User.objects.filter(**filter_kwargs)    
        return Response(serializers.UserFaceStatusSerializer(users, many=True).data)

    # ✅ 등록 API
    @action(detail=False, methods=["post"], url_path="register_via_rpc")
    @transaction.atomic
    def register_via_rpc(self, request):
        """
        대표 이미지 + (추가 이미지들) 등록
        1. 대표 이미지 저장
        2. 증강 or 추가 이미지 저장
        3. 모든 embedding 평균 → UserFace.embedding 업데이트
        """
        user_id = request.data.get("user_id")
        rep_image = request.FILES.get("representative_image")
        extra_images = request.FILES.getlist("extra_images")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        created_files = []   # rollback: 파일 경로
        extra_instances = [] # rollback: FaceImage instance

        try:
            # ✅ UserFace 생성 만, 업데이트는 없음==> 이미 있으면 삭제 후 신규로 진행.
            old_queryset = self.MODEL.objects.filter(user=user)
            old_queryset.delete()

            # ✅ UserFace 생성
            user_face = self.MODEL.objects.create(user=user)
            if rep_image:
                user_face.representative_image = rep_image
                user_face.save()
                created_files.append(user_face.representative_image.path)

            # ✅ 추가 이미지 저장
            for img in extra_images:
                fi = models.FaceImage.objects.create(user_face=user_face, image=img)
                fi.save()
                created_files.append(fi.image.path)
                extra_instances.append(fi)
            
            request_data = {
                "id": user_face.id,
                "user_id": user_id,
                "image_path": App_util.get_relative_path(user_face.representative_image.path) ,
                "extra_paths": [ 
                        {"id": fi.id, "path": App_util.get_relative_path(fi.image.path)}
                        for fi in extra_instances
                ]
            }
            rpc_response = register_face_via_grpc(request_data)
            if rpc_response.status == "success":
                result = App_util.save_from_rpc_response(rpc_response)
                if result['status'] == "success":
                    return Response(status=status.HTTP_200_OK, data=result)
                else:
                    return Response({"error": result['detail']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": rpc_response.error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        except Exception as e:
            # ✅ 예외 발생 시 rollback
            for inst in extra_instances:
                inst.delete()
            for file_path in created_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            if 'user_face' in locals():
                user_face.delete()
            return Response({"error": f"register 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ✅ 등록 API
    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        """
        대표 이미지 + (추가 이미지들) 등록
        1. 대표 이미지 저장
        2. 증강 or 추가 이미지 저장
        3. 모든 embedding 평균 → UserFace.embedding 업데이트
        """
        user_id = request.data.get("user_id")
        rep_image = request.FILES.get("representative_image")
        extra_images = request.FILES.getlist("extra_images")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        created_files = []   # rollback: 파일 경로
        extra_instances = [] # rollback: FaceImage instance

        try:
            # ✅ UserFace 생성 만, 업데이트는 없음==> 이미 있으면 삭제 후 신규로 진행.
            self.MODEL.objects.filter(user=user).delete()

            # ✅ UserFace 생성
            user_face = self.MODEL.objects.create(user=user)
            if rep_image:
                user_face.representative_image = rep_image
                user_face.save()
                created_files.append(user_face.representative_image.path)

            # ✅ 추가 이미지 저장
            for img in extra_images:
                fi = models.FaceImage.objects.create(user_face=user_face, image=img)
                fi.save()
                created_files.append(fi.image.path)
                extra_instances.append(fi)
            print ("extra_instances:", len(extra_instances))
            # ✅ Redis PUB
            sub_count = self.redis_publisher.publish(
                channel="broadcast:request_analyze",
                message={
                    "id": user_face.id,
                    "user_id": user_id,
                    "image_path": user_face.representative_image.path if user_face.representative_image else None,
                    "extra_paths": [ {"id": fi.id, "path": fi.image.path} for fi in extra_instances]
                }
            )

            # ✅ SUB 없음 → rollback
            if sub_count == 0:
                for inst in extra_instances:
                    inst.delete()
                for file_path in created_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                user_face.delete()
                return Response({"error": "register 진행중 오류 발생: worker 없음"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # ✅ 정상 진행
            return Response(
                {"message": "register 진행중 입니다.", "ws_url": REDIS_CHANNEL_RESPONSE},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # ✅ 예외 발생 시 rollback
            for inst in extra_instances:
                inst.delete()
            for file_path in created_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            if 'user_face' in locals():
                user_face.delete()
            return Response({"error": f"register 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_face_recognize_data(self, request) -> tuple[bool, dict]:
        """
        얼굴 로그인 데이터 추출
        """
        try:
            ws_url = request.data.get("ws_url", "")
            images = request.FILES.getlist("images")
            print("images:", images)
            print("ws_url:", ws_url)
            if not images:
                return False, {"error": "No image provided"}
            
            saved_paths = []
            for idx, img_file in enumerate(images):
                # 안전하게 media/tmp/ai_face 아래에 저장
                fName = f"face_login_{idx}_{int(datetime.now().timestamp())}.jpg"
                tmp_path = os.path.join(MEDIA_TMP_DIR, fName)
                with open(tmp_path, "wb") as f:
                    for chunk in img_file.chunks():
                        f.write(chunk)
                saved_paths.append(f"{SAVE_ROOT}/{fName}")
            
            result = {
                "image_paths": saved_paths,
                "ws_url": ws_url,
            }
            return True, result
        except Exception as e:
            error_str = f"face-login 진행중 오류 발생: {str(e)}"
            print(error_str)
            return False, {"error": error_str}


    @action(detail=False, methods=["post"], url_path="facelogin", permission_classes=[AllowAny])
    def facelogin(self, request):
        """
        얼굴 로그인 API
        """
        try:
            success, data = self.get_face_recognize_data(request)
            if not success:
                return Response({"error": data["error"]}, status=status.HTTP_400_BAD_REQUEST)

            sub_count = self.redis_publisher.publish(
                channel="face-login:recognize",
                message= data
            )
            if sub_count == 0:
                return Response({"error": "face-login 진행중 오류 발생: worker 없음"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(status=status.HTTP_200_OK, data={"message": "face-login 진행중 입니다."})
        except Exception as e:
            error_str = f"face-login 진행중 오류 발생: {str(e)}"
            print(error_str)
            return Response({"error": error_str}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="facelogin_via_rpc", permission_classes=[AllowAny])
    def facelogin_via_rpc(self, request):
        """
        얼굴 로그인 API
        """
        try:
            success, request_data = self.get_face_recognize_data(request)
            if not success:
                return Response({"error": request_data["error"]}, status=status.HTTP_400_BAD_REQUEST)

            rpc_response = recognize_face_via_grpc(request_data)
            if rpc_response.success:
                # Proto → dict 변환
                response_dict = MessageToDict(rpc_response, preserving_proto_field_name=True)
                # 문자열 ID → int 변환
                if "recognized_user_id" in response_dict:
                    response_dict["recognized_user_id"] = int(response_dict["recognized_user_id"])

                for d in response_dict.get("decision_images", []):
                    if "user_id" in d:
                        d["user_id"] = int(d["user_id"])
                    if "id" in d:
                        d["id"] = int(d["id"])

                # ✅ gRPC 에서 넘어온 user_id 로 로그인 토큰 발급
                try:
                    user = User.objects.get(id=response_dict["recognized_user_id"])
                except User.DoesNotExist:
                    return Response({"error": "user not found"}, status=status.HTTP_404_NOT_FOUND)
                from users.serializers import CustomTokenObtainPairSerializer
                serializer = CustomTokenObtainPairSerializer(
                    context={"user": user}  # ← 비밀번호 인증 안 하고 직접 user 주입
                )
                token_data = serializer.validate(attrs={})  # username/password 불필요

                return Response(status=status.HTTP_200_OK, data=token_data)
            else:
                return Response({"error": rpc_response.error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            error_str = f"face-login 진행중 오류 발생: {str(e)}"
            print(error_str)
            return Response({"error": error_str}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="recognize_via_rpc" )
    def recognize_via_rpc(self, request):
        """
        얼굴 인식 API
        """
        try:
            success, request_data = self.get_face_recognize_data(request)
            if not success:
                return Response({"error": request_data["error"]}, status=status.HTTP_400_BAD_REQUEST)
            rpc_response = recognize_face_via_grpc(request_data)
            if rpc_response.success:
                # Proto → dict 변환
                response_dict = MessageToDict(rpc_response, preserving_proto_field_name=True)
                for d in response_dict.get("decision_images", []):
                    if "user_id" in d:
                        d["user_id"] = int(d["user_id"])
                    if "id" in d:
                        d["id"] = int(d["id"])
                    if 'request_image' in d:
                        d['request_image'] = App_util.get_media_url(d['request_image'])
                return Response(status=status.HTTP_200_OK, data=response_dict)
            else:
                return Response({"error": rpc_response.error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            error_str = f"recognize 진행중 오류 발생: {str(e)}"
            print(error_str)
            return Response({"error": error_str}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # ✅ 인식 API
    @action(detail=False, methods=["post"], url_path="recognize")
    def recognize(self, request):
        """
        입력 이미지 → embedding 추출 → DB와 비교 → 최적 user 반환
        """
        print( request.FILES)
        ws_url = request.data.get("ws_url")
        images = request.FILES.getlist("images")
        if not images:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
        

        saved_paths = []
        for idx, img_file in enumerate(images):
            # 안전하게 media/tmp/ai_face 아래에 저장
            tmp_path = os.path.join(MEDIA_TMP_DIR, f"probe_{idx}_{int(datetime.now().timestamp())}.jpg")
            with open(tmp_path, "wb") as f:
                for chunk in img_file.chunks():
                    f.write(chunk)
            saved_paths.append(tmp_path)

        # ✅ Redis PUB
        sub_count = self.redis_publisher.publish(
            channel="broadcast:request_recognize",
            message={
                # "id": user_face.id,
                # "user_id": user_id,
                "image_paths": saved_paths,
                "ws_url": ws_url,
            }
        )
        if sub_count == 0:
            return Response({"error": "recognize 진행중 오류 발생: worker 없음"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK, data={"message": "recognize 진행중 입니다.", 'ws_url': ws_url})


        # query_emb = extract_embedding(img)

        # # DB UserFace 전체와 비교
        # min_dist = 9999
        # matched_user = None

        # for uf in self.MODEL.objects.exclude(embedding__isnull=True):
        #     db_emb = np.array(uf.embedding, dtype=np.float32)
        #     dist = np.linalg.norm(query_emb - db_emb)  # L2 거리
        #     if dist < min_dist:
        #         min_dist = dist
        #         matched_user = uf.user

        # if matched_user:
        #     return Response({
        #         "user_id": matched_user.id,
        #         "username": matched_user.username,
        #         "distance": float(min_dist)
        #     })




# from deepface import DeepFace

# # 1. 얼굴 임베딩 추출
# embedding = DeepFace.represent(img_path="media/ai/faces/person1.jpg", model_name="ArcFace", enforce_detection=False)
# print("Embedding shape:", len(embedding[0]['embedding']))

# # 2. 얼굴 비교 (인식 테스트)
# result = DeepFace.verify(img1_path="media/ai/faces/person1.jpg", img2_path="media/ai/faces/person2.jpg", model_name="ArcFace", enforce_detection=False)
# print("Same person? ->", result["verified"], " | Distance:", result["distance"])