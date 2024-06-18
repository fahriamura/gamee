import requests
import urllib.parse
import json
import time
import subprocess
import threading

# URL dan headers
url = "https://api.service.gameeapp.com/"
headers = {
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Client-Language": "en",
    "Content-Type": "application/json",
    "Origin": "https://prizes.gamee.com",
    "Referer": "https://prizes.gamee.com/",
    "X-Install-Uuid": "5dd191d7-1d6d-48fd-afa6-fcd82aba2fa7"
}

# Fungsi untuk membaca initData dari file
def read_initdata_from_file(filename):
    initdata_list = []
    with open(filename, 'r') as file:
        for line in file:
            initdata_list.append(line.strip())
    return initdata_list

# Fungsi untuk mengambil id dari initData
def get_user_id_from_init_data(init_data):
    parsed_data = urllib.parse.parse_qs(init_data)
    if 'user' in parsed_data:
        user_data = parsed_data['user'][0]
        user_data_json = urllib.parse.unquote(user_data)
        user_data_dict = json.loads(user_data_json)
        if 'id' in user_data_dict:
            return user_data_dict['id']
    return None

def get_nama_from_init_data(init_data):
    parsed_data = urllib.parse.parse_qs(init_data)
    if 'user' in parsed_data:
        user_data = parsed_data['user'][0]
        data = ""
        user_data_json = urllib.parse.unquote(user_data)
        user_data_dict = json.loads(user_data_json)
        if 'first_name' in user_data_dict:
            data = user_data_dict['first_name']
        if 'last_name' in user_data_dict:
            data = data + " " + user_data_dict['last_name']
        if 'username' in user_data_dict:
            data = data + " " + f"({user_data_dict['username']})"
    return data

# Fungsi untuk melakukan login menggunakan initData
def login_with_initdata(init_data, token):
    payload = {
        "jsonrpc": "2.0",
        "id": f"{token}",
        "method": "user.authentication.loginUsingTelegram",
        "params": {
            "initData": "user=%7B%22id%22%3A765551722%2C%22first_name%22%3A%22Amura%22%2C%22last_name%22%3A%22Fachry%20%24MEH%20%24CFI%22%2C%22username%22%3A%22absol225%22%2C%22language_code%22%3A%22id%22%2C%22allows_write_to_pm%22%3Atrue%7D&chat_instance=-3501296207680078073&chat_type=sender&start_param=6&auth_date=1716996283&hash=7252a79acd7888aef8ebd92410b293a1a884dff8cd3406d8128f4e86c88b8d02"
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        # Menambahkan header Authorization dari hasil response login
        auth_token = response.json()["result"]["tokens"]["authenticate"]
        headers["Authorization"] = f"Bearer {auth_token}"
    else:
        print(f"Failed to login. Error: {response.text}")
    return response

# Fungsi untuk melakukan start session
def start_session():
    payload = {
        "jsonrpc": "2.0",
        "id": "miningEvent.startSession",
        "method": "miningEvent.startSession",
        "params": {"miningEventId": 7}
    }
    response = requests.post(url, json=payload, headers=headers)
    return response

# Fungsi untuk mengambil hadiah
def get_prize():
    payload = [
        {"jsonrpc": "2.0", "id": "dailyReward.claimPrize", "method": "dailyReward.claimPrize", "params": {}},
        {"jsonrpc": "2.0", "id": "dailyReward.getPrizes", "method": "dailyReward.getPrizes", "params": {}}
    ]
    response = requests.post(url, json=payload, headers=headers)
    return response

# Fungsi untuk menjalankan operasi untuk setiap initData
def process_initdata(init_data):
    # Login
    token = get_user_id_from_init_data(init_data)
    nama = get_nama_from_init_data(init_data)
    if token:
        login_response = login_with_initdata(init_data, token)
        if login_response.status_code == 200:
            print(f"Logged in successfully for user id: {nama}")
            
            # Start session
            start_response = start_session()
            print(start_response.text)
            if start_response.status_code == 200:
                start_data = start_response.json()
                print(f"Tiket : {start_data['user']['tickets']['count']}")
                print(f"Usd : {start_data['user']['money']['usdCents']/100}$")
                if 'error' in start_data:
                    reason = start_data['error']['data']['reason']
                    print(f"Start session error: {reason}")
                else:
                    print('Start Mining')

                # Get prize
                prize_response = get_prize()
                
                if prize_response.status_code == 200:
                    prize_data_list = prize_response.json()
                    if 'error' in prize_data_list:
                        reason = prize_data_list["error"].get("message", "No error message provided")
                        print(f"GetPrize Error message: {reason}")
                    else:
                        payload2 = {"jsonrpc": "2.0", "id": "dailyReward.buySpinUsingTickets", "method": "dailyReward.buySpinUsingTickets", "params": {}}
                        response2 = requests.post(url, json=payload2, headers=headers)
                       # if response2.status_code == 200:
                        #    response_json2 = response2.json()
                         #   if "error" in response_json2:
                          #      error_message = response_json2["error"].get("message", "No error message provided")
                           #     print(f"BuySpin Error message: {error_message}")
                           # else:
                            #    print("Spin bought successfully.")
                            
                else:
                     print("Failed to retrieve prizes.")

            else:
                print(f"Failed to start session. Error: {start_response.text}")
        else:
            print(f"Failed to login. Error: {login_response.text}")
    else:
        print(f"Failed to get user id from initData: {init_data}")

# Main program
def main():
    initdata_file = "initdata.txt"
    
    while True:
        initdata_list = read_initdata_from_file(initdata_file)
        
        threads = []
        for init_data in initdata_list:
            thread = threading.Thread(target=process_initdata, args=(init_data.strip(),))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Delay sebelum membaca ulang file initData
        time.sleep(0)  # Delay 60 detik sebelum membaca kembali file initData

if __name__ == "__main__":
    try: 
        main()
    except Exception as e:
        subprocess.run(["py","gamee.py"])
