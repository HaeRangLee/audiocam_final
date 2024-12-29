import requests
import base64
import qrcode

# GitHub credentials
GITHUB_USERNAME = 'HaeRangLee'
GITHUB_TOKEN = ''

# Repository details
REPO_NAME = 'image-hosting'
BRANCH = 'main'  # Use 'master' if that's your default branch
# FILE_PATH_IN_REPO = 'ydp4cuts.png'  # Path where the image will be uploaded
# LOCAL_IMAGE_PATH = 'templates/ydp4cuts.png'   # Local path to your image file

def upload_image_to_github(image_path):
    file_path_in_repo = image_path.split('/')[-1]


    flag, download_url = check_file_in_github(file_path_in_repo)
    
    if flag:
        print('File already exists in the GitHub repository.')
        qr_fpath = generate_qr_code(download_url, f"{image_path[:-4]}_qr.png")
        return download_url, qr_fpath
    
    else:
        print('File does not exist in the GitHub repository.')
        with open(image_path, 'rb') as file:
            content = file.read()
        content_encoded = base64.b64encode(content).decode('utf-8')

        url = f'https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{file_path_in_repo}'

        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Content-Type': 'application/json'
        }

        data = {
            'message': 'Add image.png',
            'content': content_encoded,
            'branch': BRANCH
        }

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 201:
            print('Image uploaded successfully!')
            # Extract the download URL
            download_url = response.json()['content']['download_url']
            qr_fpath = f"{image_path[:-4]}_qr.png"
            print('Download URL:', download_url)
            generate_qr_code(download_url, qr_fpath)
            return download_url, qr_fpath
        else:
            print('Failed to upload image.')
            print('Response:', response.text)
            return None

def generate_qr_code(data, output_file):
    qr = qrcode.QRCode(
        version=None,  # Adjust size automatically
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    img.save(output_file)
    print(f'QR code saved as {output_file}')
    return output_file

def check_file_in_github(file_path_in_repo):
    url = f'https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/{BRANCH}/{file_path_in_repo}'
    print(url)
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    # Include authorization header if using a token (optional for public repos)
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print('File exists in the GitHub repository.')
        return True, url
    elif response.status_code == 404:
        print('File does not exist in the GitHub repository.')
        return False, url
    else:
        print(f'Unexpected status code: {response.status_code}')
        print('Response:', response.text)
        return False, url

if __name__ == '__main__':
    upload_image_to_github('10-17-20-49.png')