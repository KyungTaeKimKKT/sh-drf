import os
import time
import grpc
from scheduler_job.jobs.grpc_dir.ping import ping_pb2_grpc, ping_pb2
import traceback
# import logging, traceback
# logger = logging.getLogger(__name__)

# async def ping_host(host:str, taskQueue:Queue, resultsQueue:Queue, timeout:int, retry:bool=False):
# 	try:
# 		delay = await ping(host, timeout)
# 		await resultsQueue.put({host:[True, int(delay*1000)]})
# 	except TimeoutError:
# 		if retry:
# 			try:
# 				delay = await ping(host, timeout)
# 				await resultsQueue.put([True, host, delay])
# 			except: await resultsQueue.put({host:[False, f"{host} timed out (retried)."]})
# 		else: await resultsQueue.put({host:[False,-1]})
# 	taskQueue.task_done()
# 	taskQueue.get_nowait()

# async def async_ping_Hosts( pingList :list[str] ) -> list:
# 	s = time.time()
# 	results = []
# 	taskQueue: Queue = Queue(maxsize=100)
# 	resultsQueue: Queue = Queue()

# 	for IP_주소 in pingList:
# 		await taskQueue.put( create_task ( 
# 			ping_host(IP_주소, taskQueue, resultsQueue, 5, False)
# 			))
# 		# result.append(ping(pingObj.get('IP_주소'), timeout=Info.PING_TIME_OUT))
	
# 	await taskQueue.join()
# 	while not resultsQueue.empty():
# 		results.append(await resultsQueue.get())
# 		resultsQueue.task_done()
# 	await resultsQueue.join()


# 	print('ping 소요시간:', int((time.time() - s)*1000), 'msec')
# 	print( 'async_ping_Hosts results:', results )
# 	return results


GRPC_TARGET = os.getenv("GRPC_TARGET", "ping.grpc.sh:5555")
def grpc_ping(ip_list:list[str]) -> dict[str, bool]:
    try:
        with grpc.insecure_channel(GRPC_TARGET) as channel:
            stub = ping_pb2_grpc.PingServiceStub(channel)
            req = ping_pb2.PingRequest(ip_list=ip_list)
            resp = stub.CheckIPs(req, timeout=3)
            return {r.target: r.reachable for r in resp.results}
    except grpc.RpcError as e:
        print(f"[grpc_ping] RPC error: {e.code().name} - {e.details()}")
        return {ip: False for ip in ip_list}


def main_job(job_id:int):
	try:
		s = time.perf_counter()
		from 모니터링.models import 사내IP
		pingList = list(사내IP.objects.values_list('IP_주소', flat=True))
		# pingList = ['192.168.10.249', '192.168.7.108', '8.8.8.8']

		result = grpc_ping(pingList)
		print( 'main result:', result )
		return {
			'log': f"ping_네트워크 작업 성공: {len(result)} : 소요시간 {int((time.perf_counter() - s)*1000)} msec",
			'redis_publish': result
		}
	except Exception as e:
		print(f"ping_네트워크 작업 실패: {e}")
		print(traceback.format_exc())
		return {
			'log': f"ping_네트워크 작업 실패: {e}",
			'redis_publish': None
		}

# if __name__ == '__main__':
# 	main_job()