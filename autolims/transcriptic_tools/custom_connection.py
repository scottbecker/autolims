from os.path import expanduser
import json
import time
import sys
import logging
logger = logging.getLogger(__name__)
from lib import setup_logging
from transcriptic.config import Connection, AnalysisException
from transcriptic import routes
from autoprotocol import Protocol

def create_launch_url(api_root, org_id, protocol_id):
    return "{api_root}/{org_id}/protocols/{protocol_id}/launch".format(**locals())

def complete_all_instructions(api_root, org_id, project_id, run_id):
    return "{api_root}/{org_id}/{project_id}/runs/{run_id}/complete_all_instructions".format(**locals())

def get_launch(api_root, org_id, protocol_id, launch_id):
    return "{api_root}/{org_id}/protocols/{protocol_id}/launch/{launch_id}".format(**locals())

def get_protocols(api_root, org_id):
    return "{api_root}/{org_id}/protocols".format(**locals())

def get_project_run(api_root, org_id, project_id, run_id):
    return "{api_root}/{org_id}/{project_id}/runs/{run_id}".format(**locals())

def conversation_posts(api_root, conversation_id):
    return "{api_root}/conversations/{conversation_id}/posts".format(**locals())

def conversation_post(api_root, conversation_id, post_id):
    return "{api_root}/conversations/{conversation_id}/posts/{post_id}".format(**locals())

routes.create_launch = create_launch_url
routes.complete_all_instructions = complete_all_instructions
routes.get_launch = get_launch
routes.get_protocols = get_protocols
routes.get_project_run = get_project_run
routes.conversation_posts = conversation_posts
routes.conversation_post = conversation_post

class CustomConnection(Connection):
    
    def __init__(self, email=None, token=None, organization_id=False, 
                api_root="https://secure.transcriptic.com", 
                organization=False, cookie=False, 
                verbose=False, use_environ=True,
                analyze_only=False,
                test_mode=True):
        """

        analyze_only tells us to not actually run submitted jobs but instead log autoprotocol and price information.
        
        To view full detail information, logger must be set to debug (info shows price and run numbers)
        
        """
        
        self.unexecuted_runs = []
        self.test_mode = test_mode
        
        self.analyze_only = analyze_only
        self._run_id_to_conversation_id_cache = {}
        
        super(CustomConnection,self).__init__(email, token, organization_id, 
                                              api_root, 
                                              organization, cookie, 
                                              verbose, use_environ)
    
    def execute_all_runs(self):
        
        if self.analyze_only:
            return
        
        for kwargs in self.unexecuted_runs:
            self.post(self.get_route('complete_all_instructions', 
                                     **kwargs),
                      status_response={
                          '200': lambda resp: resp,
                          '201': lambda resp: resp,
                          'default': lambda resp: Exception("[%d] %s" % (resp.status_code, resp.text)),
            
                          '404': lambda resp: AnalysisException("Error: Couldn't complete instructions (404). \n"
                                                                "Are you sure the project %s "
                                                                "exists, and that you have access to it?" %
                                                                self.url(project_id)),
                          '422': lambda resp: AnalysisException("Error completing instructions for run: %s" % resp.text)
                      }            
                      )   
            
        self.unexecuted_runs = []
    
    @staticmethod
    def from_file(path):
        """Loads connection from file"""
        with open(expanduser(path), 'r') as f:
            cfg = json.loads(f.read())
            return CustomConnection(**cfg)    
        
        
    #custom version that prevents ssl verification
    @staticmethod
    def _req_call(method, route, **kwargs):
        
        if 'verify' not in kwargs:
            kwargs['verify'] = False
            
        return Connection._req_call(method, route, **kwargs)   


    def protocols(self):
        """Get list of projects in organization"""
        route = self.get_route('get_protocols')
        return self.get(route, status_response={
                'default': lambda resp: RuntimeError(
                    "There was an error fetching protocols"
                )
            })   


    def launch(self,protocol_id,launch_id):
        route = self.get_route('get_launch', protocol_id=protocol_id,launch_id=launch_id)
        return self.get(route, status_response={
                'default': lambda resp: RuntimeError(
                    "There was an error fetching launch %s" % launch_id
                )
            })        

    def submit_package_run(self, project_id, protocol_id, title,parameters=None,test_mode=True,
                           bsl=1):
        """Create and submit a launch of a given protocol
        
        Returns a json object describing the run that was created
        
        
        Won't actually submit if self.analyze_only is True (returns None)
        
        """
        
        #submit the launch request

        launch_response = self.post(self.get_route('create_launch', protocol_id=protocol_id),
                                    data=json.dumps({
                                        "launch_request": {
                                        #title isn't used here in the UI but its mentioned in the docs
                                        #"title": title,
                                        "parameters": parameters,
                                        "test_mode": test_mode,
                                        "bsl": bsl,
                                        }}),
                                    status_response={
                                        '404': lambda resp: AnalysisException("Error: Couldn't create launch (404). \n"
                                                                              "Are you sure the project %s "
                                                                              "exists, and that you have access to it?" %
                                                                              self.url(project_id)),
                                        '422': lambda resp: AnalysisException("Error creating launch: %s" % resp.text)
                                    })       
        
        launch_id = launch_response['id']
        
        
        #launch_response = {'progress':0}
        #launch_id = 'lr1988gg7rpygf'
        
        
        #wait for the launch to be created
        
        while launch_response['progress'] != 100:
            time.sleep(1)
            launch_response = self.launch(protocol_id, launch_id)
        
        #create the run
        
        if launch_response.get('generation_errors'):
            for error in launch_response['generation_errors']:
                error['info'] = error.get('info','').replace('\\n','\n')
                sys.stderr.write(error['message']+'\n')
                sys.stderr.write(error['info'])
            sys.exit(1) 
            
            
        run_analysis = self.analyze_run(launch_response['autoprotocol'],
                                        test_mode=self.test_mode,
                                        bsl=bsl)
        
        total = run_analysis['quote']['breakdown']['total']
        logger.info('Preparing to submit run: %s  \n Cost: $%s \nParams: %s'%(title,total,json.dumps(parameters)))
        logger.debug("autoprotocol is \n %s"%launch_response['autoprotocol'])
        logger.debug("cost information is \n %s"%run_analysis)
        
        if not self.analyze_only:
            logger.info('submitting run: %s'%title)
            transcriptic_run = self.post(self.get_route('submit_run', project_id=project_id),
                             data=json.dumps({
                                 "title": title,
                                 "protocol_id": protocol_id,
                                 "launch_request_id": launch_id,
                                 "test_mode": test_mode
                                 }),
                             status_response={
                                 '404': lambda resp: AnalysisException("Error: Couldn't create run (404). \n"
                                                                       "Are you sure the project %s "
                                                                       "exists, and that you have access to it?" %
                                                                       self.url(project_id)),
                                 '422': lambda resp: AnalysisException("Error creating run: %s" % resp.text)
                             })
            
            if test_mode:
                
                run_kwargs = {
                    'project_id': project_id,
                    'run_id': transcriptic_run['id']
                }
                self.unexecuted_runs.append(run_kwargs)
                
            return transcriptic_run, run_analysis
        else:
            return None, run_analysis
        
    #same as transcriptic version with bsl status added
    def analyze_run(self, protocol, test_mode=False, bsl=1):
        """Analyze given protocol"""
        if isinstance(protocol, Protocol):
            protocol = protocol.as_dict()
        if "errors" in protocol:
            raise AnalysisException(("Error%s in protocol:\n%s" %
                                     (("s" if len(protocol["errors"]) > 1 else ""),
                                      "".join(["- " + e['message'] + "\n" for
                                               e in protocol["errors"]]))))
    
        def error_string(r):
            return AnalysisException("Error%s in protocol:\n%s" %
                                     (("s" if len(r.json()['protocol']) > 1 else ""),
                                      "".join(["- " + e['message'] + "\n" for e in r.json()['protocol']])
                                      ))
    
        return self.post(self.get_route('analyze_run'),
                         data=json.dumps({
                             "protocol": protocol,
                             "test_mode": test_mode,
                             "bsl": bsl
                             }),
                         status_response={'422': lambda response: error_string(response)})     


    def run(self, project_id, run_id):
        """Get list of runs in project"""
        route = self.get_route('get_project_run', project_id=project_id, run_id=run_id)
        return self.get(route, status_response={
            "200": lambda resp: resp.json(),
            "default": lambda resp: RuntimeError(
                "There was an error fetching the run %s in project %s" %
                (run_id, project_id)
            )
        })
    
    def get_launch_for_run(self, project_id, run_id, protocol_id):
        run = self.run(project_id, run_id)
        return self.launch(protocol_id, run['launch_request_id'])
    
    def get_output_containers(self, project_id, run_id, protocol_id):
        
        run = self.run(project_id, run_id)
        launch = self.launch(protocol_id, run['launch_request_id'])
        
        container_lookup = {}
        
        for container in run['refs']:
            container_lookup[container['name']] = container
        
        output_containers = []
        for name, container in launch['autoprotocol']['refs'].items():
            
            if container.get('discard'):
                continue
            
            if container.get('id'):
                continue
            
            #retrieve the new id of the container
            
            output_containers.append(container_lookup[name])
            
                 
        return output_containers
    
    def _get_conversation_for_run(self, project_id, run_id):
        if run_id not in self._run_id_to_conversation_id_cache:
            run = self.run(project_id, run_id)
            self._run_id_to_conversation_id_cache[run_id] = run['conversation_id']            
        
        return self._run_id_to_conversation_id_cache[run_id]
    
    def create_post(self, project_id, run_id, post_text):
        conversation_id = self._get_conversation_for_run(project_id, run_id)
        
        conversation = self.post(self.get_route('conversation_posts', conversation_id=conversation_id),
                                     data=json.dumps({
                                         "post": {
                                                 "text": post_text,
                                                 "viewable_by_users": True,
                                                 "attachments": {
                                                         "attachments": []
                                                 }
                                         }
                                 }),
                                    status_response={
                                         '404': lambda resp: AnalysisException("Error: Couldn't create post (404)."),
                                         '422': lambda resp: AnalysisException("Error creating post: %s" % resp.text)
                                     })        
        
        return conversation
        
    
    def posts(self, project_id, run_id):
        conversation_id = self._get_conversation_for_run(project_id, run_id)
        route = self.get_route('conversation_posts', conversation_id = conversation_id)
        return self.get(route, status_response={
            "200": lambda resp: resp.json(),
            "default": lambda resp: RuntimeError(
                "There was an error fetching the conversation in run %s in project %s" %
                (run_id, project_id)
            )
        }) 
    
    
    def delete_post(self, project_id, run_id, post_id):
        conversation_id = self._get_conversation_for_run(project_id, run_id)
        
        conversation = self.delete(self.get_route('conversation_post', conversation_id=conversation_id, 
                                                  post_id=post_id),
                                    status_response={
                                        '200': lambda resp: True
                                    })        
        
              
              
    def get_raw_file(self, data_id, file_path):
        """
        Get zip file with given data_id. Downloads to memory and returns a Python ZipFile by default.
        When dealing with larger files where it may not be desired to load the entire file into memory,
        specifying `file_path` will enable the file to be downloaded locally.
    
        Example Usage:
    
        .. code-block:: python
    
            small_zip_id = 'd12345'
            small_zip = api.get_zip(small_zip_id)
    
            my_big_zip_id = 'd99999'
            api.get_zip(my_big_zip_id, file_path='big_file.zip')
    
        Parameters
        ----------
        data_id: data_id
            Data id of file to download
        file_path: Optional[str]
            Path to file which to save the response to. If specified, will not return ZipFile explicitly.
    
        Returns
        ----------
        zip: zipfile.ZipFile
            A Python ZipFile is returned unless `file_path` is specified
    
        """
        import zipfile
        from io import BytesIO
        route = self.get_route('get_data_zip', data_id=data_id)
        req = self.get(route, status_response={'200': lambda resp: resp}, stream=True)
        if file_path:
            f = open(file_path, 'wb')
            # Buffer download of data into memory with smaller chunk sizes
            chunk_sz = 1024  # 1kb chunks
            for chunk in req.iter_content(chunk_sz):
                if chunk:
                    f.write(chunk)
            f.close()
            print("Zip file downloaded locally to {}.".format(file_path))
        else:
            return zipfile.ZipFile(BytesIO(req.content))    