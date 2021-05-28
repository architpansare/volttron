
import re
import json
from os import environ
from os.path import normpath, join
from gevent.timeout import Timeout
from urllib.parse import parse_qs

from volttron.platform.agent.known_identities import PLATFORM_WEB, AUTH, CONFIGURATION_STORE
from werkzeug import Response
from volttron.platform.vip.agent.subsystems.query import Query
from volttron.platform.jsonrpc import MethodNotFound
from volttron.platform.web.topic_tree import TopicTree


import logging
_log = logging.getLogger(__name__)


class VUIEndpoints(object):
    def __init__(self, agent=None):
        self._agent = agent
        q = Query(self._agent.core)
        self.local_instance_name = q.query('instance-name').get(timeout=5)
        # TODO: Load active_routes from configuration. Default can just be {'vui': {'endpoint-active': False}}
        self.active_routes = {
            'vui': {
                'endpoint-active': True,
                'platforms': {
                    'endpoint-active': True,
                    'agents': {
                        'endpoint-active': True,
                        'configs': {
                            'endpoint-active': False,
                        },
                        'enabled': {
                            'endpoint-active': False,
                        },
                        'front-ends': {
                            'endpoint-active': False,
                        },
                        'health': {
                            'endpoint-active': False,
                        },
                        'pubsub': {
                            'endpoint-active': True,
                        },
                        'rpc': {
                            'endpoint-active': True,
                        },
                        'running': {
                            'endpoint-active': False,
                        },
                        'status': {
                            'endpoint-active': False,
                        },
                        'tag': {
                            'endpoint-active': False,
                        }
                    },
                    'auths': {
                        'endpoint-active': False,
                    },
                    'configs': {
                        'endpoint-active': False,
                    },
                    'devices': {
                        'endpoint-active': True,
                    },
                    'groups': {
                        'endpoint-active': False,
                    },
                    'health': {
                        'endpoint-active': False,
                    },
                    'historians': {
                        'endpoint-active': True,
                    },
                    'known-hosts': {
                        'endpoint-active': False,
                    },
                    'pubsub': {
                        'endpoint-active': True,
                    },
                    'roles': {
                        'endpoint-active': False,
                    },
                    'status': {
                        'endpoint-active': False,
                    },
                    'statistics': {
                        'endpoint-active': False,
                    }
                },
                'devices': {
                    'endpoint-active': True,
                },
                'historians': {
                    'endpoint-active': True,
                }
            }
        }

    def get_routes(self):
        """
        Returns a list of tuples with the routes for the administration endpoints
        available in it.

        :return:
        """
        # TODO: Break this up into appends to allow configuration of which endpoints are available.
        _log.debug('In VUIEndpoints.get_routes()')
        return [
            (re.compile('^/vui/?$'), 'callable', self.handle_vui_root),
            (re.compile('^/vui/platforms/?$'), 'callable', self.handle_platforms),
            (re.compile('^/vui/platforms/[^/]+/?$'), 'callable', self.handle_platforms_platform),
            (re.compile('^/vui/platforms/[^/]+/agents/?$'), 'callable', self.handle_platforms_agents),
            (re.compile('^/vui/platforms/[^/]+/agents/[^/]+/?$'), 'callable', self.handle_platforms_agents_agent),
            (re.compile('^/vui/platforms/[^/]+/agents/[^/]+/rpc/?$'), 'callable', self.handle_platforms_agents_rpc),
            (re.compile('^/vui/platforms/[^/]+/agents/[^/]+/rpc/[^/]+/?$'), 'callable', self.handle_platforms_agents_rpc_method),
            (re.compile('^/vui/platforms/[^/]+/devices/?$'), 'callable', self.handle_platforms_devices),
            (re.compile('^/vui/platforms/[^/]+/devices/.*/?$'), 'callable', self.handle_platforms_devices),
            # (re.compile('^/vui/platforms/[^/]+/historians/?$'), 'callable', self.handle_platforms_historians),
            # (re.compile('^/vui/platforms/[^/]+/historians/[^/]+/?$'), 'callable', self.handle_platforms_historians_historian),
            # (re.compile('^/vui/platforms/[^/]+/historians/[^/]+/topics/?$'), 'callable', self.handle_platforms_historians_topics),
            # (re.compile('^/vui/platforms/[^/]+/historians/[^/]+/topics/.+/?$'), 'callable', self.handle_platforms_historians_topics_topic),
            # (re.compile('^/vui/platforms/[^/]+/historians/[^/]+/history/?$'), 'callable', self.handle_platforms_historians_history),
            # (re.compile('^/vui/platforms/[^/]+/pubsub(/.*/)?$'), 'callable', self.handle_platforms_pubsub),
            # (re.compile('^/vui/platforms/[^/]+/pubsub(/.*/)?$'), 'callable', self.handle_platforms_pubsub_topic),
            # (re.compile('^/vui/devices/?$'), 'callable', self.handle_vui_devices),
            # (re.compile('^/vui/devices/.+/?$'), 'callable', self.handle_vui_devices_topic),
            # (re.compile('^/vui/devices/hierarchy/?$'), 'callable', self.handle_vui_devices_hierarchy),
            # (re.compile('^/vui/devices/hierarchy/.+/?$'), 'callable', self.handle_vui_devices_hierarchy_topic),
            # (re.compile('^/vui/historians/?$'), 'callable', self.handle_vui_historians),
            # (re.compile('^/vui/history/?$), 'callable', self.handle_vui_history)
        ]

    def handle_vui_root(self, env: dict, data: dict) -> Response:
        _log.debug('VUI: In handle_vui_root')
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        if request_method == 'GET':
            path_info = env.get('PATH_INFO')
            response = json.dumps(self._find_active_sub_routes(['vui'], path_info=path_info))
            return Response(response, 200, content_type='application/json')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    def handle_platforms(self, env: dict, data: dict) -> Response:
        _log.debug('VUI: In handle_platforms')
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        if request_method == 'GET':
            platforms = []
            try:
                with open(join(environ['VOLTTRON_HOME'], 'external_platform_discovery.json')) as f:
                    platforms = [platform for platform in json.load(f).keys()]
            except FileNotFoundError:
                _log.info('Did not find VOLTTRON_HOME/external_platform_discovery.json. Only local platform available.')
            except Exception as e:
                _log.warning(f'Error opening external_platform_discovery.json: {e}')
            finally:
                if self.local_instance_name not in platforms:
                    platforms.insert(0, self.local_instance_name)
            response = json.dumps({p: normpath(path_info + '/' + p) for p in platforms})
            return Response(response, 200, content_type='application/json')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    def handle_platforms_platform(self, env: dict, data: dict) -> Response:
        _log.debug('VUI: In handle_platforms_platform')
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        if request_method == 'GET':
            response = json.dumps(self._find_active_sub_routes(['vui', 'platforms'], path_info=path_info))
            return Response(response, 200, content_type='application/json')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    def handle_platforms_agents(self, env: dict, data: dict) -> Response:
        """
        Endpoints for /vui/platforms/:platform/agents/
        :param env:
        :param data:
        :return:
        """
        # TODO: The API specification calls for a "packaged" query parameter that will return packaged agents which
        #  could be installed. We can get that from os.listdir(VOLTTRON_HOME/packaged), but skipping for now since
        #  there is no POST to the endpoint right now anyway.
        _log.debug('VUI: In handle_platforms_agents')
        _log.debug(env)
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        platform = re.match('^/vui/platforms/([^/]+)/agents/?$', path_info).groups()[0]
        if request_method == 'GET':
            agents = self._get_agents(platform)
            # TODO: How to catch invalid platform. The routing service seems to catch the exception and just log an
            #  error without raising it. Can we get a list of external platforms from somewhere? Again, the routing
            #  service seems to have that, but it isn't exposed as an RPC call anywhere that I can find....
            # return Response(json.dumps({'error': f'Platform: {platform} did not respond to request for agents.'}),
            #                400, content_type='application/json')
            response = json.dumps({agent: normpath(path_info + '/' + agent) for agent in agents.keys()})
            return Response(response, 200, content_type='application/json')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    def handle_platforms_agents_agent(self, env: dict, data: dict) -> Response:
        """
        Endpoints for /vui/platforms/:platform/agents/:vip_identity/
        :param env:
        :param data:
        :return:
        """
        _log.debug('VUI: In handle_platforms_agents_agent')
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        platform, vip_identity = re.match('^/vui/platforms/([^/]+)/agents/([^/]+)/?$', path_info).groups()
        # TODO: Check whether this agent is actually running.
        # TODO: Check whether certain types of actions are actually available for this agent (or require next endpoint for this)?
        if request_method == 'GET':
            response = json.dumps(self._find_active_sub_routes(['vui', 'platforms', 'agents'], path_info=path_info))
            return Response(response, 200, content_type='application/json')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    def handle_platforms_agents_rpc(self, env: dict, data: dict) -> Response:
        """
        Endpoints for /vui/platforms/:platform/agents/:vip_identity/rpc/
        :param env:
        :param data:
        :return:
        """
        _log.debug('VUI: In handle_platforms_agents_rpc')
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        platform, vip_identity = re.match('^/vui/platforms/([^/]+)/agents/([^/]+)/rpc/?$', path_info).groups()
        if request_method == 'GET':
            try:
                method_dict = self._rpc(vip_identity, 'inspect', on_platform=platform)
            # TODO: Move this exception handling up to a wrapper.
            except TimeoutError as e:
                return Response(json.dumps({'error': f'Request Timed Out: {e}'}), 408, content_type='application/json')
            except Exception as e:
                return Response(json.dumps({'error' f'Unexpected Error: {e}'}), 500, content_type='application/json')

            response = {method: normpath(path_info + '/' + method) for method in (method_dict.get('methods'))}
            return Response(json.dumps(response), 200, content_type='application/json')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    def handle_platforms_agents_rpc_method(self, env: dict, data: dict) -> Response:
        """
        Endpoints for /vui/platforms/:platform/agents/:vip_identity/rpc/
        :param env:
        :param data:
        :return:
        """
        _log.debug("VUI: in handle_platform_agents_rpc_method")
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        platform, vip_identity, method_name = re.match('^/vui/platforms/([^/]+)/agents/([^/]+)/rpc/([^/]+)/?$',
                                                       path_info).groups()
        _log.debug(f'VUI: Parsed - platform: {platform}, vip_identity: {vip_identity}, method_name: {method_name}')
        if request_method == 'GET':
            try:
                _log.debug('VUI: request_method was "GET"')
                method_dict = self._rpc(vip_identity, method_name + '.inspect', on_platform=platform)
                _log.debug(f'VUI: method_dict is: {method_dict}')
            # TODO: Move this exception handling up to a wrapper.
            except Timeout as e:
                return Response(json.dumps({'error': f'RPC Timed Out: {e}'}), 408, content_type='application/json')
            except MethodNotFound as e:
                return Response(json.dumps({f'error': f'for agent {vip_identity}: {e}'}),
                                400, content_type='application/json')
            except Exception as e:
                return Response(json.dumps({'error' f'Unexpected Error: {e}'}), 500, content_type='application/json')

            return Response(json.dumps(method_dict), 200, content_type='application/json')

        elif request_method == 'POST':
            # TODO: Should this also support lists?
            data = data if type(data) is dict else {}
            try:
                _log.debug('VUI: request_method was "POST')
                _log.debug(f'VUI: data has type: {type(data)}, value: {data}')
                result = self._rpc(vip_identity, method_name, **data, on_platform=platform)
            except Timeout as e:
                return Response(json.dumps({'error': f'RPC Timed Out: {e}'}), 408, content_type='application/json')
            except MethodNotFound as e:
                return Response(json.dumps({f'error': f'for agent {vip_identity}: {e}'}),
                                400, content_type='application/json')
            except Exception as e:
                return Response(json.dumps({'error' f'Unexpected Error: {e}'}), 500, content_type='application/json')

            return Response(json.dumps(result), 200, content_type='application/json')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    def handle_platforms_devices(self, env: dict, data: dict) -> Response:
        """
        Endpoints for /vui/platforms/:platform/devices/ and /vui/platforms/:platform/devices/:topic/
        :param env:
        :param data:
        :return:
        """
        _log.debug("VUI: in handle_platform_devices")
        path_info = env.get('PATH_INFO')
        request_method = env.get("REQUEST_METHOD")
        no_topic = re.match('^/vui/platforms/([^/]+)/devices/?$', path_info)
        if no_topic:
            platform, topic = no_topic.groups()[0], ''
        else:
            platform, topic = re.match('^/vui/platforms/([^/]+)/devices/(.*)/?$', path_info).groups()
            topic = topic[:-1] if topic[-1] == '/' else topic
        _log.debug(f'VUI: Parsed - platform: {platform}, topic: {topic}')

        if request_method == 'GET':
            try:
                devices = self._rpc(CONFIGURATION_STORE, 'manage_list_configs', 'platform.driver', on_platform=platform)
                devices = [d for d in devices if re.match('^devices/.*', d)]
                _log.debug(f'Devices from rpc: {devices}')
                # TODO: Should we be storing this tree to use for faster requests later? How to keep it updated?
                device_tree = TopicTree(devices, 'devices')
                for d in devices:
                    # TODO: Getting points requires getting device config, using it to find the registry config,
                    #  and then parsing that. There is not a method in config.store, nor in the platform.driver for
                    #  getting a completed configuration. The configuration is only fully assembled in the subsystem's
                    #  _intial_update method called when the agent itself calls get_configs at startup. There does not
                    #  seem to be an equivalent management method, and the code for this is in the agent subsystem
                    #  rather than the service (though it is reached through the service, oddly...
                    dev_config = json.loads(
                        self._rpc('config.store', 'manage_get', 'platform.driver', d, on_platform=platform))
                    reg_cfg_name = dev_config.get('registry_config')[len('config://'):]
                    _log.debug(f'Fetching registry for: {reg_cfg_name}')
                    registry_config = self._rpc('config.store', 'manage_get', 'platform.driver',
                                                f'registry_configs/{reg_cfg_name}', raw=False, on_platform=platform)
                    for pnt in registry_config:
                        point_name = pnt['Volttron Point Name']
                        device_tree.create_node(point_name, f"{d}/{point_name}", parent=d)
                # TODO: Handle query parameters for changing the output.
                # TODO: We should have a query parameter for returning partial vs full topics as the key.
                # TODO: We should have a query parameter for returning one level vs full tree.
                _log.debug(device_tree.to_json(with_data=True))
                topic_node_id = f'devices/{topic}' if topic else 'devices'
                topic_node = device_tree.get_node(topic_node_id)
                if topic_node and topic_node.is_leaf():
                    # TODO: Handle case of this being a leaf node (should that be device or point?)

                    return Response(f'Endpoint {request_method} {path_info} does not yet implement leaf behavior.',
                                    status='501 Not Implemented', content_type='text/plain')
                else:
                    route_dict = device_tree.get_children_dict(topic_node_id, prefix=f'/vui/platforms/{platform}')
                    if route_dict:
                        return Response(json.dumps(route_dict), 200, content_type='application/json')
                    elif topic:
                        return Response(
                            json.dumps({f'error': f'Device topic {topic} not found on platform: {platform}.'}),
                            400, content_type='application/json')
                    else:
                        return Response(json.dumps({f'error': f'Unable to retrieve devices for platform: {platform}.'}),
                                        400, content_type='application/json')

            # TODO: Move this exception handling up to a wrapper.
            except Timeout as e:
                return Response(json.dumps({'error': f'RPC Timed Out: {e}'}), 408, content_type='application/json')
            except Exception as e:
                return Response(json.dumps({f'error': f'Error querying device topic {topic}: {e}'}),
                                400, content_type='application/json')

        elif request_method == 'PUT':
            # TODO: Implement PUT.
            # TODO: For put requests, we should have a configuration to disallow mass sets.
            # TODO: For put requests, we should also return a route for DELETE to reset the action later.
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')
        elif request_method == 'DELETE':
            # TODO: Implement DELETE.
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')
        else:
            return Response(f'Endpoint {request_method} {path_info} is not implemented.',
                            status='501 Not Implemented', content_type='text/plain')

    # TODO: Will _find_segments() be needed? This may be superceded by the TopicTree, (at least for topic uses)?
    @staticmethod
    def _find_segments(path_info):
        match = re.match('/([^/]+)/?', path_info)
        if match:
            groups = match.groups()
            if groups:
                return [x for x in groups[0].split('/') if x]

    def _find_active_sub_routes(self, segments: list, path_info: str = None) -> dict or list:
        """
        Returns active routes with constant segments at the end of the route.
                If no path_info is provided, return only a list of the keys.
        """
        route_obj = self.active_routes
        for segment in segments:
            if route_obj and route_obj.get(segment) and route_obj.get(segment).get('endpoint-active'):
                route_obj = route_obj.get(segment)
            else:
                return {}
        keys = [k for k in route_obj.keys() if k != 'endpoint-active' and route_obj[k]['endpoint-active']]
        if not path_info:
            return keys
        else:
            return {k: normpath(path_info + '/' + k) for k in keys}

    # TODO: Add running parameter.
    def _get_agents(self, platform, running=True):
        _log.debug(f'VUI._get_agents: local_instance_name is: {self.local_instance_name}')
        try:
            agent_list = self._rpc('control', 'list_agents', on_platform=platform)
            peerlist = self._rpc('control', 'peerlist', on_platform=platform)
        except TimeoutError:
            agent_list = []
            peerlist = []
        except Exception as e:
            agent_list = []
            peerlist = []
            _log.debug(f'VUI._get_agents - UNEXPECTED EXCEPTION: {e}')
        agent_dict = {}
        _log.debug('VUI._get_agents: agent_list: {}'.format(agent_list))
        _log.debug('VUI._get_agents: peerlist: {}'.format(peerlist))
        # TODO: Add option to include system agents (e.g., control) instead of just installed or packaged agents?
        for agent in agent_list:
            agent_id = agent.pop('identity')
            agent['running'] = True if agent_id in peerlist else False
            agent_dict[agent_id] = agent
        return agent_dict

    def _rpc(self, agent, method, *args, on_platform=None, **kwargs):
        external_platform = {'external_platform': on_platform}\
            if on_platform != self.local_instance_name else {}
        result = self._agent.vip.rpc.call(agent, method, *args, **external_platform, **kwargs).get(timeout=5)
        return result

    # def admin(self, env, data):
    #     if env.get('REQUEST_METHOD') == 'POST':
    #         decoded = dict((k, v if len(v) > 1 else v[0])
    #                        for k, v in parse_qs(data).items())
    #         username = decoded.get('username')
    #
    # def verify_and_dispatch(self, env, data):
    #     """ Verify that the user is an admin and dispatch"""
    #
    #     from volttron.platform.web import get_bearer, NotAuthorized
    #     try:
    #         claims = self._rpc_caller(PLATFORM_WEB, 'get_user_claims', get_bearer(env)).get()
    #     except NotAuthorized:
    #         _log.error("Unauthorized user attempted to connect to {}".format(env.get('PATH_INFO')))
    #         return Response('<h1>Unauthorized User</h1>', status="401 Unauthorized")
    #
    #     # Make sure we have only admins for viewing this.
    #     if 'admin' not in claims.get('groups'):
    #         return Response('<h1>Unauthorized User</h1>', status="401 Unauthorized")
    #
    #     path_info = env.get('PATH_INFO')
    #     if path_info.startswith('/admin/api/'):
    #         return self.__api_endpoint(path_info[len('/admin/api/'):], data)
    #
    #     return Response(resp)
