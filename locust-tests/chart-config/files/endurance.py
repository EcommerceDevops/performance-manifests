from locust import HttpUser, task, between
import random

class WebUser(HttpUser):
    wait_time = between(1, 3)

    # Tareas más frecuentes (peso 10)
    @task(10)
    def get_all_users(self):
        self.client.get("/user-service/api/users")

    @task(10)
    def get_all_addresses(self):
        self.client.get("/user-service/api/address")

    # Tareas menos frecuentes (peso 1 por defecto)
    @task
    def get_user_by_id(self):
        # Es mejor usar IDs dinámicos en lugar de siempre el '1'
        user_id = random.randint(1, 4) # Suponiendo que tienes 4 usuarios
        self.client.get(f"/user-service/api/users/{user_id}", name="/user-service/api/users/[id]")

    @task
    def get_address_by_id(self):
        address_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/address/{address_id}", name="/user-service/api/address/[id]")

    @task
    def get_all_credentials(self):
        self.client.get("/user-service/api/credentials")

    @task
    def get_credential_by_id(self):
        credential_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/credentials/{credential_id}", name="/user-service/api/credentials/[id]")

    @task
    def get_all_verification_tokens(self):
        self.client.get("/user-service/api/verificationTokens")

    @task
    def get_verification_token_by_id(self):
        token_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/verificationTokens/{token_id}", name="/user-service/api/verificationTokens/[id]")