# ark
![image](ark.jpg)

## 创建
```shell
ark create run.arkio.demo
```
## WSGI

### 启动
```shell
ark serve --wsgi
or
gunicorn demo.app:app --reload
```

### 测试
```shell
curl "http://127.0.0.1:8000/"
```

### 压测
```shell
ab -n 10000 -c 100 -t 10 "http://127.0.0.1:8000/"
```

## GRPC
### 启动
```shell
ark serve
```

### 测试
```shell
grpcurl -plaintext 127.0.0.1:50051 list

grpcurl -plaintext -d '{"name": "ark"}' 127.0.0.1:50051 helloworld.Greeter/SayHello
grpcurl -plaintext -d '{"name": "redis"}' 127.0.0.1:50051 helloworld.Greeter/SayHello
grpcurl -plaintext -d '{"name": "kafka"}' 127.0.0.1:50051 helloworld.Greeter/SayHello
grpcurl -plaintext -d '{"name": "rabbit"}' 127.0.0.1:50051 helloworld.Greeter/SayHello

grpcurl -plaintext -d '{"name": "ark"}' 127.0.0.1:50051 helloworld.Greeter/SayHelloAsync
grpcurl -plaintext -d '{"name": "rpc"}' 127.0.0.1:50051 helloworld.Greeter/SayHelloAsync
```


### 压测
```shell
# ecs.c6.large 2vCPU/4GiB
ghz --insecure --async \
    --call helloworld.Greeter/SayHello \
    -c 1000 -n 20000 --rps 5000 \
    -d '{"name":"ark"}' 172.26.1.198:50051
```
## 运行模式
* ark serve --wsgi
* ark serve
* ark worker
* ark consumer
* ark shell
* ark run
* ark test
* ark lint


## 基础设施

### redis
```shell
docker run -d --hostname redis --name redis -p 6379:6379 redis
```

### rabbitmq
```shell
docker run -d --hostname rabbit --name rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
[后台] http://127.0.0.1:15672

### kafka
```shell
export KAFKA_ADVERTISED_HOST_NAME=172.26.1.199

docker rm -f kafka
docker rm -f zookeeper
docker run -d --name zookeeper -p 2181:2181 -t wurstmeister/zookeeper
docker run -d --name kafka -p 9092:9092 --link zookeeper -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 -e KAFKA_ADVERTISED_HOST_NAME=$KAFKA_ADVERTISED_HOST_NAME -e KAFKA_ADVERTISED_PORT=9092 wurstmeister/kafka:2.12-2.4.0

docker exec -it kafka bash
kafka-topics.sh --zookeeper zookeeper:2181 --list
kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic topic01
kafka-topics.sh --zookeeper zookeeper:2181 --create --topic topic01 --replication-factor 1 --partitions 5
```

### elasticsearch
```shell
docker run --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -d elasticsearch:7.2.0

curl http://localhost:9200
```

### elasticsearch-kibana
```shell
docker run --name kibana --link=elasticsearch:test  -p 5601:5601 -d kibana:7.2.0
```
[后台] http://127.0.0.1:15672

## 必备工具
### grpcurl
```shell
# mac
brew install grpcurl

# linux
https://github.com/fullstorydev/grpcurl/releases/download/v1.8.6/grpcurl_1.8.6_linux_x86_64.tar.gz
```
[文档] https://github.com/fullstorydev/grpcurl

### ghz
```shell
# mac
brew install ghz

# linux
wget https://github.com/bojand/ghz/releases/download/v0.108.0/ghz-linux-x86_64.tar.gz
```
[文档] https://ghz.sh/docs/usage


### protobuf
```shell
# mac
brew install protobuf

# linux
PROTOC_ZIP=protoc-3.14.0-osx-x86_64.zip
curl -OL https://github.com/protocolbuffers/protobuf/releases/download/v3.14.0/$PROTOC_ZIP
sudo unzip -o $PROTOC_ZIP -d /usr/local bin/protoc
sudo unzip -o $PROTOC_ZIP -d /usr/local 'include/*'
rm -f $PROTOC_ZIP
```
[文档] http://google.github.io/proto-lens/installing-protoc.html
