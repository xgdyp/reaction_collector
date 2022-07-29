import requests
import json 
from collections import Counter,defaultdict
from configparser import ConfigParser
import threading

class ReactionCollector:
    def __init__(self,token:int) -> None:
        self.d = defaultdict(Counter)
        self.v3headers = {
            'Accept': 'application/vnd.github.v3.text+json',
            'Authorization': 'token {}'.format(token),
            'User-Agent': 'apifox/1.0.0 (https://www.apifox.cn)'
        }

        self.headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': 'token {}'.format(token),
            'User-Agent': 'apifox/1.0.0 (https://www.apifox.cn)'
        }
        self.payload = dict()
        self.total_issue_num = 0
        self.total_issue_page = 0
        self.issue_comment_id_set = set()
        self.issue_list = list()
        self.pr_list = list()
        self.issue_num_set = set()
        self.pr_num_set  = set()
    def save_issue_list(self):
        with open('issue_list.json', 'w') as f:
            json.dump(self.issue_list, f)

    def save_pr_list(self):
        with open('pr_list.json', 'w') as f:
            json.dump(self.issue_list, f)
    def write_to_test_file(self,text):
        with open("test","w") as f:
            f.write(text)
    def collect_issue_body_reactions(self,owner,repo,issue_number: int) -> dict:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/reactions?per_page=100"

        response = requests.get(url, headers=self.headers, data=self.payload)
        data = response.json()
        # reactions = data["reactions"]
        print(url)
        for reaction in data:
            self.d[reaction["user"]["login"]][reaction["content"]] += 1
    
        return self.d

    def collect_issue_comment_id(self,owner,repo,issue_number: int) -> list:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments?per_page=100"
        response = requests.get(url, headers=self.headers, data=self.payload)
        data = response.json()
        comment_id = set()
        for comment in data:
            comment_id.add(comment["id"])
        return comment_id



    def collect_comment_reactions(self,owner,repo,comment_id) -> dict:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions?per_page=100"
        # url = f"https://api.github.com/repos/hypertrons/hypertrons-crx/issues/comments/{i}/reactions?per_page=100"

        print(url)
        response = requests.get(url, headers=self.headers, data=self.payload)
        # data = response.json()
        self.process_reaction_result(response)
        # comment_reactions = defaultdict(Counter)
        # for comment in data:
        #     print('here')
        #     print(comment)

        #     comment_reactions[comment["id"]] = defaultdict(Counter)
        #     for reaction in comment["reactions"]:
        #         comment_reactions[comment["id"]][reaction["user"]["login"]][reaction["content"]] += 1
        # return comment_reactions

    def process_reaction_result(self,response):
        if response == None:
            return None
        for reaction in response.json():
            if "user" not in reaction:
                print(reaction)
                continue
            self.d[reaction["user"]["login"]][reaction["content"]] += 1
        return self.d

    def collect_issue_pr_reactions(self):
        #for each issue, we get its reactions
        #we get commentid set from each issue
        #first we collect issue body reactions
        # then we collect comment reactions
        for i in r.issue_num_set:
            print("---start get issue comment id---")
            print("currently processing issue number: ",i)
            comment_set = self.collect_issue_comment_id(owner,repo,i)
            print(i,comment_set)
            # r.issue_comment_id_dict = r.issue_comment_id_set.union(collect_issue_comment_id("hypertrons","hypertrons-crx",i))
            self.collect_issue_body_reactions(owner,repo,i)
            for comment_id in comment_set:
                self.collect_comment_reactions(owner,repo,comment_id)
        # then we do the same thing in pr
        for i in r.pr_num_set:
            print("start get pr comment id")
            print("currently processing pr number: ",i)
            self.collect_issue_body_reactions(owner,repo,i)
            comment_set = self.collect_issue_comment_id(owner,repo,i)
            print(i,comment_set)
            for comment_id in comment_set:
                self.collect_comment_reactions(owner,repo,comment_id)

    def collect_num(self,owner,repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?page=1&per_page=10&state=all"
        response = requests.get(url, headers=r.v3headers, data=r.payload)
        data = response.json()
        self.total_issue_num=int(data[0].get("number"))
        print(self.total_issue_num)
        # get total page of an issue
        self.total_issue_page = self.total_issue_num // 100 + 1

    def get_issue_pr_set(self,owner,repo):
    # get issue and pr set 
    # in v3 api, issue and pr are in the same endpoint
    # we can check if response data have "pull_request" key to determine if it is an issue or pr
        for i in range(1,r.total_issue_page+1):
            url = f"https://api.github.com/repos/{owner}/{repo}/issues?page={i}&per_page=100&state=all"
            response = requests.get(url, headers=r.v3headers, data=r.payload)
            data = response.json()
            for item in data:
                print(item.get('number'))
                if "pull_request" not in item:
                    self.issue_list.append(item)
                    self.issue_num_set.add(int(item.get('number')))
                else:
                    self.pr_list.append(item)
                    self.pr_num_set.add(int(item.get('number')))    
    def print_total(self):
        for k,v in self.d.items():
            print(k,sum(v.values()))

    def start_task(self,owner,repo):
        self.collect_num(owner,repo)
        self.get_issue_pr_set(owner,repo)
        self.collect_issue_pr_reactions()
        self.save_issue_list()
        self.save_pr_list()
        self.print_total()



def load_config():
    config = ConfigParser()
    config.read('env.ini')
    print("get token")
    return config.get("github", "token")

    

    
if __name__ == "__main__":
    print('start here')
    print('read token from .env')
    token = load_config()

    rst = []
    owner = "X-lab2017"
    repo_list = ["DesignThinking-LeanStartup","open-research","open-digger","open-wonderland"]
    # repo = "DesignThinking-LeanStartup"
    for repo  in repo_list:
        r = ReactionCollector(token)
        # t=threading.Thread(target=r.start_task,args=(owner,repo))
        # t.start()
        r.start_task(owner,repo)
        r.print_total()
        rst.append((r.d,repo))

    for item,name in rst:
        print(name)
        for k,v in item.items():
            print(k,sum(v.values()))
    print('----end----')


