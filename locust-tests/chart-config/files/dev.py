from locust import HttpUser, task, between
import random

class WebUser(HttpUser):
    wait_time = between(1, 3)
    @task
    def getHome(self):
        self.client.get("/")