import aiohttp
import asyncio
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

doc_list = []
hour_of_update = 0
minute_for_update = 0


class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

    def json(self):
        return {
            'page_content': self.page_content,
            'metadata': self.metadata
        }


def clean_text(text):
    cleaned_text = re.sub(r'\s{2,}', ' ', text)
    cleaned_text = re.sub(r'[\n\r]{2,}', '\n', cleaned_text)
    return cleaned_text


def html_parser(data):
    soup = BeautifulSoup(data, 'html.parser')
    return soup.get_text(separator='\n')


def getting_web_ui_content(page_html_content):
    soup = BeautifulSoup(page_html_content, 'html.parser')
    headers = [header.get_text(strip=True) for level in range(1, 7) for header in soup.find_all(f'h{level}')]
    paragraphs = [para.get_text(strip=True) for para in soup.find_all('p')]
    links = [{'text': link.get_text(strip=True), 'url': link['href']} for link in soup.find_all('a', href=True)]
    return headers, paragraphs, links


# async def fetch(session, url):
#     async with session.get(url) as response:
#         content_type = response.headers.get('Content-Type', '')
#         if 'application/json' in content_type:
#             return await response.json()
#         else:
#             return await response.text()
async def fetch(session, url):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return await response.json()
            else:
                return await response.text()
    except aiohttp.client_exceptions.ClientOSError as e:
        print(f"Skipping URL due to ClientOSError: {url} - {e}")
        return None
    except asyncio.TimeoutError:
        print(f"Request timed out for URL: {url}")
        return None
    except aiohttp.ClientError as e:
        print(f"Client error for URL {url}: {e}")
        return None


async def connect_to_web_ui_link(session, base_url, web_ui_link, try_num, page_number, post_number, title, links,
                                 hour_of_update, minute_for_update):
    if try_num != 1:
        print(f"\n That URL : {web_ui_link} has an error in connection , So we are trying again ... Try No. {try_num}")

    web_ui_content = await fetch(session, web_ui_link)

    if web_ui_content is None:
        print(f"Skipping further processing for URL: {web_ui_link} due to previous errors.")
        return

    if isinstance(web_ui_content, dict):
        print("Received JSON response for a web UI link, which is unexpected.")
        return

    first_level_headers, first_level_paragraphs, first_level_links = getting_web_ui_content(web_ui_content)
    using_html_parser = html_parser(web_ui_content)
    doc_list.append(Document(page_content=clean_text(using_html_parser), metadata={
        "source": f"Page #{page_number} , Post No.{post_number}",
        "title": title,
        "links": web_ui_link,
        "page_number": str(page_number),
        "post_number": str(post_number),
        "hour_of_update": str(hour_of_update),
        "minute_for_update": str(minute_for_update)
    }))

    for para in first_level_paragraphs:
        words = para.split()
        if len(words) > 5:
            doc_list.append(Document(page_content=para, metadata={
                "source": f"Page #{page_number} , Post No.{post_number}",
                "title": title,
                "links": web_ui_link,
                "page_number": str(page_number),
                "post_number": str(post_number),
                "hour_of_update": str(hour_of_update),
                "minute_for_update": str(minute_for_update)
            }))

    for link in first_level_links:
        second_level_url = base_url + link['url'].replace("/wiki/wiki", "/wiki", 1)
        second_level_content = await fetch(session, second_level_url)
        if second_level_content is None:
            print(f"Skipping second-level URL due to previous errors: {second_level_url}")
            continue
        if isinstance(second_level_content, dict):
            print("Received JSON response for a second-level link, which is unexpected.")
            continue
        second_level_headers, second_level_paragraphs, second_level_links = getting_web_ui_content(second_level_content)
        using_html_parser = html_parser(second_level_content)
        doc_list.append(Document(page_content=clean_text(using_html_parser), metadata={
            "source": f"Page #{page_number} , Post No.{post_number}",
            "title": title,
            "links": web_ui_link,
            "page_number": str(page_number),
            "post_number": str(post_number),
            "hour_of_update": str(hour_of_update),
            "minute_for_update": str(minute_for_update)
        }))

        for para in second_level_paragraphs:
            words = para.split()
            if len(words) > 20 and len(words) != 0:
                doc_list.append(Document(page_content=para, metadata={
                    "source": f"Page #{page_number} , Post No.{post_number}",
                    "title": title,
                    "links": web_ui_link,
                    "page_number": str(page_number),
                    "post_number": str(post_number),
                    "hour_of_update": str(hour_of_update),
                    "minute_for_update": str(minute_for_update)
                }))


# async def connect_to_web_ui_link(session, base_url, web_ui_link, try_num, page_number, post_number, title, links,
#                                  hour_of_update, minute_for_update):
#     if try_num != 1:
#         print(f"\n That URL : {web_ui_link} has an error in connection , So we are trying again ... Try No. {try_num}")
#     web_ui_content = await fetch(session, web_ui_link)
#
#     if isinstance(web_ui_content, dict):
#         print("Received JSON response for a web UI link, which is unexpected.")
#         return
#
#     first_level_headers, first_level_paragraphs, first_level_links = getting_web_ui_content(web_ui_content)
#     using_html_parser = html_parser(web_ui_content)
#     doc_list.append(Document(page_content=clean_text(using_html_parser), metadata={
#         "source": f"Page #{page_number} , Post No.{post_number}",
#         "title": title,
#         "links": web_ui_link,
#         "page_number": str(page_number),
#         "post_number": str(post_number),
#         "hour_of_update": str(hour_of_update),
#         "minute_for_update": str(minute_for_update)
#     }))
#
#     for para in first_level_paragraphs:
#         words = para.split()
#         if len(words) > 5:
#             doc_list.append(Document(page_content=para, metadata={
#                 "source": f"Page #{page_number} , Post No.{post_number}",
#                 "title": title,
#                 "links": web_ui_link,
#                 "page_number": str(page_number),
#                 "post_number": str(post_number),
#                 "hour_of_update": str(hour_of_update),
#                 "minute_for_update": str(minute_for_update)
#             }))
#
#     for link in first_level_links:
#         second_level_url = base_url + link['url'].replace("/wiki/wiki", "/wiki", 1)
#         second_level_content = await fetch(session, second_level_url)
#         if isinstance(second_level_content, dict):
#             print("Received JSON response for a second-level link, which is unexpected.")
#             continue
#         second_level_headers, second_level_paragraphs, second_level_links = getting_web_ui_content(second_level_content)
#         using_html_parser = html_parser(second_level_content)
#         doc_list.append(Document(page_content=clean_text(using_html_parser), metadata={
#             "source": f"Page #{page_number} , Post No.{post_number}",
#             "title": title,
#             "links": web_ui_link,
#             "page_number": str(page_number),
#             "post_number": str(post_number),
#             "hour_of_update": str(hour_of_update),
#             "minute_for_update": str(minute_for_update)
#         }))
#
#         for para in second_level_paragraphs:
#             words = para.split()
#             if len(words) > 20 and len(words) != 0:
#                 doc_list.append(Document(page_content=para, metadata={
#                     "source": f"Page #{page_number} , Post No.{post_number}",
#                     "title": title,
#                     "links": web_ui_link,
#                     "page_number": str(page_number),
#                     "post_number": str(post_number),
#                     "hour_of_update": str(hour_of_update),
#                     "minute_for_update": str(minute_for_update)
#                 }))


async def getting_main_250_posts(session, confluence_page_api, page_counter, hour_of_update, minute_for_update):
    async with session.get(confluence_page_api) as response:
        if 'application/json' in response.headers.get('Content-Type', ''):
            confluence_page_data = await response.json()
        else:

            await getting_main_250_posts(session, confluence_page_api, page_counter, hour_of_update, minute_for_update)
            # print("Received non-JSON response.")
            # print(response)
            # return

    if response.status == 200:
        print("We are Connected to the API ...")
        print("Now We can access ", len(confluence_page_data['results']), " Posts in Page ", page_counter)

        next_links_dict = confluence_page_data.get('_links', {})

        tasks = []
        for post in range(len(confluence_page_data['results'])):
            links = confluence_page_data['results'][post].get("_links", {})
            title = confluence_page_data['results'][post].get("title", {})
            web_ui = links['webui']
            web_ui_link = next_links_dict['base'] + web_ui
            print(f"\nTitle For Post No.{post + 1} in Page#{page_counter} ...", title)
            print(
                f"\n\nNow let's Fetch Data from our Web Ui link No.{post + 1} From Page #{page_counter} in our First Result list ",
                web_ui_link)
            tasks.append(
                connect_to_web_ui_link(session, next_links_dict['base'], web_ui_link, 1, page_counter, post + 1, title,
                                       links, hour_of_update, minute_for_update))

        await asyncio.gather(*tasks)

        if 'next' in next_links_dict:
            url = next_links_dict['next']
            cursor_value = None
            for part in url.split('&'):
                if 'cursor=' in part:
                    cursor_value = part.split('=')[1]
                    break

            confluence_page_api = f"https://expertflow-docs.atlassian.net/wiki/api/v2/pages?limit=250&cursor={cursor_value}"
            page_counter += 1
            await getting_main_250_posts(session, confluence_page_api, page_counter, hour_of_update, minute_for_update)
        else:
            print(f"We have Reached to Page {page_counter}.")
            save_docs_to_json(doc_list, 'general_file_iterable_250_posts.json')


def save_docs_to_json(array, file_path):
    json_data = [doc.json() for doc in array]
    with open(file_path, 'w') as json_file:
        json.dump(json_data, json_file)


def read_json_file(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)


def save_old_file_in_backup_folder(filePath):
    json_data = read_json_file(filePath)
    hour_of_update = str(json_data[-1]['metadata']['hour_of_update'])
    minute_for_update = str(json_data[-1]['metadata']['minute_for_update'])
    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    new_filename = f'old_file_{current_datetime}.json'
    backup_folder = 'backups'
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    new_file_path = os.path.join(backup_folder, new_filename)
    os.rename(filePath, new_file_path)
    print(f'File has been renamed to {new_filename} and moved to {backup_folder}')
    return hour_of_update, minute_for_update


def seconds_until_midnight(hour, minute):
    tomorrow = datetime.now() + timedelta(1)
    midnight = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=hour, minute=minute, second=0)
    return (midnight - datetime.now()).total_seconds()


async def main():
    filePath = "general_file_iterable_250_posts.json"
    async with aiohttp.ClientSession() as session:
        if os.path.isfile(filePath):
            confluence_page_api = "https://expertflow-docs.atlassian.net/wiki/api/v2/pages?limit=250"
            hour_of_update, minute_for_update = save_old_file_in_backup_folder(filePath)
            await getting_main_250_posts(session, confluence_page_api, 1, hour_of_update, minute_for_update)
        else:
            hour_of_update = int(input("Enter the hour for update: "))
            minute_for_update = int(input("Enter the minutes of update hour: "))
            confluence_page_api = "https://expertflow-docs.atlassian.net/wiki/api/v2/pages?limit=250"
            await getting_main_250_posts(session, confluence_page_api, 1, hour_of_update, minute_for_update)


if __name__ == "__main__":
    asyncio.run(main())
