import json
import redis

# from src.api.api import cache

cache = redis.Redis(host='redis', port=6379)


def get_neighbors(name, exclude_self=True):
    neighbors = cache.get('nodes')
    neighbors = json.loads(neighbors) if neighbors else []
    neighbors = list({v['_name']: v for v in neighbors}.values())  # return unique list of nodes

    found = list(filter(lambda node: node['_name'] == name, neighbors))  # check if node already exist in list
    if len(found) == 0:
        neighbors.append({'_name': name})
        cache.set('nodes', json.dumps(neighbors))

    if exclude_self:
        neighbors = list(filter(lambda node: node['_name'] != name, neighbors))  # exclude node form list of neighbors

    return neighbors


def save_leader(leader):
    leaders = cache.get('leader')
    leaders = json.loads(leaders) if leaders else {}
    current_term_leader = leaders.get(f"{leader['term']}", None)

    if current_term_leader:
        if leader['timestamp'] > current_term_leader['timestamp'] and leader['no_of_votes'] and \
                leader['no_of_votes'] >= current_term_leader['no_of_votes']:
            leaders[f"{leader['term']}"] = leader
    else:
        leaders[f"{leader['term']}"] = leader

    cache.set('leader', json.dumps(leaders))


def save_election(ballots, candidate, term):
    ballots = [ballot if hasattr(ballot, '__getitem__') else None for ballot in ballots]
    election = cache.get('election')
    election = json.loads(election) if election else {}
    current_term_election = election.get(f'{term}', [])

    current_term_election.append({
        'term': term,
        'ballots': ballots,
        '_name': candidate,
    })

    election[f'{term}'] = current_term_election
    cache.set('election', json.dumps(election))