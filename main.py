import asyncio
import socket
from datetime import datetime
from data import projects, languages, librariesAndFrameworks, tools

PORT = 6379
HOST = "127.0.0.1"

clients = set()
start_time = datetime.now()

COMMANDS = {
    "ABOUT": "Display information about Manan Gandhi",
    "CHAT": "Start a conversation with the chatbot",
    "COMMAND": "List all available commands",
    "HELLO": "Get server information and protocol details",
    "INFO": "Display server information",
    "PROJECTS": "List projects or get details about a specific project",
    "SKILLS": "Display skills categorized by languages, libraries, frameworks, and tools",
}


async def handle_client(client, addr):
    clients.add(client)

    try:
        await send_message(
            client,
            """
███╗   ███╗ █████╗ ███╗   ██╗ █████╗ ███╗   ██╗ ██████╗  █████╗ ███╗   ██╗██████╗ ██╗  ██╗██╗
████╗ ████║██╔══██╗████╗  ██║██╔══██╗████╗  ██║██╔════╝ ██╔══██╗████╗  ██║██╔══██╗██║  ██║██║
██╔████╔██║███████║██╔██╗ ██║███████║██╔██╗ ██║██║  ███╗███████║██╔██╗ ██║██║  ██║███████║██║
██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║╚██╗██║██║   ██║██╔══██║██║╚██╗██║██║  ██║██╔══██║██║
██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╔╝██║  ██║██║ ╚████║██████╔╝██║  ██║██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═╝
""",
        )
        while True:
            data = await asyncio.get_event_loop().sock_recv(client, 1024)
            if not data:
                break

            command_str = data.decode("utf-8").strip()
            command_parts = command_str.split()

            command = command_parts[0] if command_parts else ""
            args = command_parts[1:] if len(command_parts) > 1 else []

            response = handle_command(command_parts, client)
            if response is not None:
                await send_message(client, response)
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        clients.remove(client)
        client.close()


async def send_message(client, message, is_end=True):
    if not message:
        return

    message = f"{message}"
    if is_end:
        message += "\n\n > "
    await asyncio.get_event_loop().sock_sendall(client, message.encode("utf-8"))


async def send_streaming_message(client, message, delay=0.1):
    words = message.split()
    for index, word in enumerate(words):
        await send_message(client, word + " ", is_end=index == len(words) - 1)
        await asyncio.sleep(delay)


def handle_command(data, client=None):
    if not data or len(data) == 0:
        return "No Command"

    command = data[0]
    args = data[1:] if len(data) > 1 else []

    match command.upper():
        case "HELLO":
            response = {
                "server": "netcat-portfolio",
                "version": "1.0.0",
                "id": id(client) if client else 0,
                "mode": "standalone",
            }
            return "\n".join([f"{k}: {v}" for k, v in response.items()])

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
            for cmd, desc in COMMANDS.items():
                response += f"## {cmd}\n{desc}\n\n"
            return response.strip()

        case "ABOUT":
            return "I am Manan Gandhi, an 18 y/o engineering student, who loves to code and build software tools."

        case "PROJECTS":
            if args:
                try:
                    project_index = int(args[0]) - 1
                    if 0 <= project_index < len(projects):
                        found_project = projects[project_index]
                        return f"""
{found_project["projectName"]}
{found_project["projectDescription"]}
• Tech Stack: {', '.join(found_project["projectTechnologies"])}
• URL: {found_project["projectLink"]}
"""
                    else:
                        return "Project not found."
                except ValueError:
                    return "Invalid project index."
            else:
                response = "These are the projects developed by me:\n"
                for index, project in enumerate(projects):
                    response += f"({index+1}) {project['projectName']} - {project['projectLink']}\n"
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
                asyncio.create_task(
                    send_streaming_message(client, "Hello! I am Manan Gandhi's Chatbot")
                )
                return None
            else:
                return "Connection error"

        case _:
            return "Invalid command"


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
