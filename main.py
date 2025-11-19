import asyncio
import socket
from datetime import datetime
from google.genai.client import Client
from google.genai import types
import os
import dotenv
import difflib
from data import projects, languages, librariesAndFrameworks, tools, banner_text, commands

PORT = 1810
HOST = "0.0.0.0"

clients = set()
chat_histories = {}
start_time = datetime.now()

dotenv.load_dotenv()
gemini_client = Client(api_key=os.environ["GEMINI_API_KEY"])

system_prompt = f"""
You are Manan Gandhi's Chatbot, running in a netcat shell
Manan Gandhi is an 19 Year Old Computer Engineering student at SVKM's NMIMS MPSTME.
Manan has been to 20 hackathons, and won 5 hackathons.
Manan's Skills: {librariesAndFrameworks, languages, tools}
Manan's Projects: {projects}

Manan's birthdate is 18th October 2006, hence the port 1810 is used on the netcat version.

Commands available for the user are:
{commands}

Do not have a very off-topic conversation with the user, refuse to answer those queries.

Links:
Website - https://manangandhi.tech
GitHub - https://github.com/MananGandhi1810
Linkedin - https://www.linkedin.com/in/manangandhi1810
Instagram - https://instagram.com/manan.py
Twitter/X - https://x.com/MananGandhi1810
"""


async def handle_client(client, addr):
    clients.add(client)
    chat_histories[client] = gemini_client.aio.chats.create(
        model="gemini-2.5-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )

    try:
        await send_message(
            client,
            banner_text,
        )
        while True:
            data = await asyncio.get_event_loop().sock_recv(client, 1024)
            if not data:
                break

            command_str = data.decode("utf-8").strip()
            command_parts = command_str.split()

            if len(command_parts) == 0:
                await send_message(client, None)
                continue

            if command_parts[0].upper() == "EXIT":
                await send_message(client, "Goodbye, hope to see you again!\n", is_end=False)
                break

            response = handle_command(command_parts, client)
            if response is not None:
                await send_message(client, response)
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        clients.remove(client)
        del chat_histories[client]
        client.close()


async def send_message(client, message, is_end=True):
    if message is None:
        await asyncio.get_event_loop().sock_sendall(client, "\n>".encode("utf-8"))
        return
    if is_end:
        message += "\n\n> "
    await asyncio.get_event_loop().sock_sendall(client, message.encode("utf-8"))


async def handle_chat(client, prompt):
    chat = chat_histories[client]
    async for chunk in await chat.send_message_stream(prompt):
        if not chunk.text:
            continue
        await send_message(client, chunk.text, is_end=False)
    await send_message(client, "")


def handle_command(data, client=None):
    if not data or len(data) == 0:
        return None

    command = data[0]
    args = data[1:] if len(data) > 1 else []

    match command.upper():
        case "HELLO":
            return "Hello! I am Manan Gandhi."

        case "INFO":
            uptime = datetime.now() - start_time
            uptime_seconds = int(uptime.total_seconds())
            return f"""Server Information
Running since: {start_time}
Uptime (seconds): {uptime_seconds}
Connected clients: {len(clients)}
Port: {PORT}
Host: {HOST}"""

        case "COMMAND":
            response = "# Available Commands\n\n"
            for cmd, desc in commands.items():
                response += f"## {cmd}\n{desc}\n\n"
            return response.strip()

        case "WHOAMI":
            return "I am Manan Gandhi, an 18 y/o engineering student, who loves to code and build software tools."

        case "PROJECTS":
            if args:
                try:
                    project_index = int(args[0]) - 1
                    if 0 <= project_index < len(projects):
                        found_project = projects[project_index]
                        response = f"""{found_project["projectName"]}
{found_project["projectDescription"]}
• Tech Stack: {', '.join(found_project["projectTechnologies"])}
"""
                        if found_project.get("link"):
                            response += f"• Live: {found_project['link']}\n"
                        if found_project.get("repo"):
                            response += f"• Repo: {found_project['repo']}\n"
                        return response
                    else:
                        return "Project not found."
                except ValueError:
                    return "Invalid project index."
            else:
                response = "These are the projects developed by me:\n"
                for index, project in enumerate(projects):
                    if project.get('link') and project.get('repo'):
                        link = f"Live: {project['link']}, Repo: {project['repo']}"
                    elif project.get('link') or project.get('repo'):
                        link = project.get('link') or project.get('repo')
                    else:
                        link = 'N/A'
                    response += f"({index+1}) {project['projectName']} - {link}\n"
                response += (
                    "Use PROJECTS <number> to get more details about each project.\n"
                )
                return response

        case "SKILLS":
            response = "Languages:\n"
            for skill in languages:
                response += f"• {skill}\n"
            response += "\nLibraries & Frameworks:\n"
            for skill in librariesAndFrameworks:
                response += f"• {skill}\n"
            response += "\nTools:\n"
            for skill in tools:
                response += f"• {skill}\n"
            return response

        case "CHAT":
            if client:
                if not args:
                    return "Please send a prompt to chat.\nExample - CHAT Who is Manan Gandhi?"
                asyncio.create_task(handle_chat(client, " ".join(args)))
                return None
            else:
                return "Connection error"

        case "HELP":
            if args:
                cmd = args[0].upper()
                if cmd in commands:
                    help_texts = {
                        "WHOAMI": "Usage: WHOAMI\nDisplays information about Manan Gandhi and his background.",
                        "CHAT": "Usage: CHAT <message>\nStart a conversation with the AI chatbot. Example: CHAT Tell me about Manan's skills",
                        "COMMAND": "Usage: COMMAND\nShows a list of all available commands with brief descriptions.",
                        "HELLO": "Usage: HELLO\nDisplays a greeting message and basic server information.",
                        "INFO": "Usage: INFO\nShows detailed server information including uptime and connected clients.",
                        "PROJECTS": "Usage: PROJECTS [number]\nList all projects or get details about a specific project by providing its number.",
                        "SKILLS": "Usage: SKILLS\nDisplays a comprehensive list of technical skills categorized by type.",
                        "RESUME": "Usage: RESUME\nProvides a link to view and download Manan Gandhi's resume.",
                        "HELP": "Usage: HELP [command]\nGet detailed help about commands. If no command is specified, shows general help.",
                    }
                    return help_texts[cmd]
                return (
                    f"Command '{cmd}' not found. Use COMMAND to see available commands."
                )
            response = "Available commands:\n\n"
            for cmd, desc in commands.items():
                response += f"{cmd}: {desc}\n"
            response += (
                "\nFor detailed help about a specific command, type: HELP <command>"
            )
            return response

        case "RESUME":
            return "You can view and download my resume here: https://manangandhi.tech/Manan_Gandhi_Resume.pdf"

        case _:
            close_matches = difflib.get_close_matches(command.upper(), commands.keys(), n=3, cutoff=0.6)
            if close_matches:
                return f"Command '{command}' not found. Did you mean: {', '.join(close_matches)}?"
            else:
                help_menu = handle_command(["HELP"])
                response = "Invalid command.\n\n" + help_menu
                return response


async def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.setblocking(False)

    server.bind((HOST, PORT))
    server.listen()

    print(f"[*] Listening on {HOST}:{PORT}")

    loop = asyncio.get_event_loop()

    while True:
        client, addr = await loop.sock_accept(server)
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

        loop.create_task(handle_client(client, addr))


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n[*] Server shutting down")
