# Raft Algorithm with "Escort Simulator"

By:
Ayomide Bakare

#### Raft Algorithm
This is an implementation of Raft Algorithm with Escort Simulator. The Leader node starts at point [0, 0] and moves to point [100, 0], one step at a time.
All other Follower nodes are positioned around the leader node and moves the save unit/direction as the Leader moves. If the Leader is lost, an elected Candidate node becomes the new Leader
and picks up where the previous Leader left off.

The nodes are docker containers each with a python server running on port 8080 (internally).
Each node can be in 3 different states at a time:
- Follower: any new node entering the raft is first a follower
- Candidate: a node becomes a candidate by starting an election. An election is only started if the Follower node
does not receive a heartbeat from the Leader after a timeout (the heartbeat timeout)
- Leader: a Candidate becomes a Leader by winning an election by majority vote.

Nodes communicate via HTTP protocol via a bridge network

#### Escort Simulator
The Leader leads the other Follower nodes by sending a message at every heartbeat to the nodes. 
The message sent by the Leader is it\'s intention to move to a new point. Immediately the majority of Followers respond,
the Leader then changes it\'s state and sends a message to the Follower to change their state to the new position too. 
This process is called Log Replication. All messages sent by the Leader are appended to a log on all nodes.

#### Peripherals
- Redis Database: stores information on nodes are in the raft, data on elections for every single term,
  and leaders elected in each election. This key value store servers as the source of truth for a Candidate or Leader node
- Proxy Server: designed to expose the Raft nodes to the external world. It also depends on the redis database to get the
  Leader node. The Proxy forwards requests from a client to the Leader node.
  The proxy also exposes an external API to get metadata and logs about the nodes, elections and term leaders in the raft.

### Requirements
- Docker: version 20.10.6, build 370c289
- Docker Compose: version 1.29.1, build c34c88b2

_**Node** docker image available on docker hub [Raft Node Image](https://hub.docker.com/r/mbao01/raft-node)_


### Setup
Currently, the number of starting Nodes (5) in this test setup is hard coded in the docker-compose.yml file.
The proxy server (http://localhost:8888) and redis database are also defined in it. To simply start with the defaults, run the following command
in the root of this project:

1. Start up
```shell
# start up nodes, proxy and redis db
$ docker compose up -d
# NOTE: the data in redis db is not persisted. 
# If you want this, modify docker-compose.yml file accordingly 
```

```shell
# to view nodes, proxy and redis db, run: 
$ docker ps
```

Open a browser and enter the proxy server address (http://localhost:8888). 
You should see a documentation of the external API showing the available endpoints

For your convenience, here are a few:

```shell
PROXY_ADDR = http://localhost:8888

1.  {
      "description": "shows the status of the external api", 
      "locator": "<PROXY_ADDR>/status", 
      "method": "GET"
    }

2.  {
      "description": "shows all nodes and leader node", 
      "locator": "<PROXY_ADDR>/nodes", 
      "method": "GET"
    }

3.  {
      "description": "shows all elections for each term", 
      "locator": "<PROXY_ADDR>/elections", 
      "method": "GET"
    }

4.  {
      "description": "shows all leaders for each term", 
      "locator": "<PROXY_ADDR>/leaders", 
      "method": "GET"
    } 
```

2. Adding new nodes <br>
   You can add new nodes to the raft. Ensure that the redis database is up.
   Here\'s the command to do that:
```shell
$ docker run -d --name=<NodeX> --network=raft-network mbao01/raft-node
# NodeX - container name for node
```

2. Remove a node from raft <br>
   You can remove nodes from the raft. It could be a leader node, to simulate a timeout and candidate election. 
   It could also be a follower node. Here\'s the command to do that:

```shell
$ docker stop <ContainerID OR NodeName>
```

### Future work
- Decouple inter-node communication/networking layer from Node
- Create interface for Node to join a decentralized network (# currently a bridge network)
- Redis Database is only setup to test here. Use any DB you wish and backup data in some storage.

### THANK YOU!

References:
- Special thanks to [@streed](https://github.com/streed) and other contributors for this [simple raft](https://github.com/streed/simpleRaft.git) repo.
- [Raft consensus algorithm website](https://raft.github.io/)
- [The Secret Lives of Data](http://thesecretlivesofdata.com/raft/) - Very good!