import base64
import bs4
import io
import json
import random
import requests
import time
import threading
from PIL import Image as PILImage, ImageTk
from tkinter import *
from tkinter import filedialog
from tkinter.font import Font

class RescenceWebBrowser:
    def __init__(self, master: Tk):
        self.master = master
        self.master.title("Rescence")

        self.master.grid_columnconfigure(0)
        self.master.grid_columnconfigure(1)
        self.master.grid_columnconfigure(2)
        self.master.grid_columnconfigure(3, weight=3)
        self.master.grid_rowconfigure(2, weight=1)
        
        self.images = []

        self.history = []
        self.history_index = -1

        self.session = requests.Session()

        self.menu = Menu(self.master)

        self.filemenu = Menu(self.menu)
        self.menu.add_cascade(label='File', menu=self.filemenu)        
        self.filemenu.add_command(label='Save', command=self.save_current_page)
        self.filemenu.add_command(label='Save as...', command=self.save_current_page_as)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit', command=self.master.destroy)

        self.back = Button(self.master, text='Back', command=self.go_back)
        self.back.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

        self.forward = Button(self.master, text='Forward', command=self.go_forward)
        self.forward.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        self.refresh = Button(self.master, text='Refresh', command=self.get_refresh)
        self.refresh.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        master.bind('<F5>', self.get_refresh)

        self.addressbar = Entry(self.master)
        self.addressbar.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        self.addressbar.bind('<Return>', self.get_website)

        self.frame = Frame(self.master)
        self.frame.grid(row=1, column=0, columnspan=4, sticky='nsew')

        self.scrollbar = Scrollbar(self.frame)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.website = Text(self.frame, height=20, width=80, wrap='word', yscrollcommand=self.scrollbar.set)
        self.website.pack(side=LEFT, fill=BOTH, expand=True)
        self.website.config(state='disabled', bg='#F0F0F0')
        self.website.tag_configure("h1", font=Font(size=32))
        self.website.tag_configure("h2", font=Font(size=24))
        self.website.tag_configure("p", font=Font(size=16))

        self.container_stack = []

        self.scrollbar.config(command=self.website.yview)

        self.screen_width = round(self.master.winfo_screenwidth() // 1.5)
        self.screen_height = round(self.master.winfo_screenheight() // 1.5)
        self.screen_x = round((self.master.winfo_screenwidth() - self.screen_width) // 2)
        self.screen_y = round((self.master.winfo_screenheight() - self.screen_height) // 2)

        self.master.config(menu=self.menu)

        self.master.geometry(f"{self.screen_width}x{self.screen_height}+{self.screen_x}+{self.screen_y}")

        print(f'[{round(time.time())}] Say hi to Rescence!')

    def get_website(self, event=None):
        def _get_website(event=None):
            starttime = time.time()

            self.website.config(state='normal')
            self.website.delete('1.0', END)
            try:
                try:
                    url = self.addressbar.get()
                    rawtext = self.session.get(url).text
                except requests.exceptions.MissingSchema:
                    if len(url.split('.')) > 1:
                        url = 'https://' + self.addressbar.get()
                        rawtext = self.session.get(url).text
                    else:
                        url = 'https://google.com/search?q=' + self.addressbar.get()
                        rawtext = self.session.get('https://google.com/search?q=' + url).text

                self.addressbar.delete(0, END)
                self.addressbar.insert(END, url)

                if event is not None:
                    self.history = self.history[:self.history_index + 1]
                    self.history.append(url)
                    self.history_index = len(self.history) - 1

                content = bs4.BeautifulSoup(rawtext, features='html.parser')

                for element in content.find_all('a', {'href': '#main-content'}):
                    element.decompose()  # Remove this element from the HTML

                for element in content.head.find_all():
                    if element.name == 'title':
                        self.master.title(f'Rescence - {element.get_text()}')

                insert_position = '1.0'

                self.container_stack = [self.website]

                for element in content.body.find_all():
                    if element.name == 'div':
                        frame = Frame(self.website)
                        self.website.window_create("insert", window=frame)
                        self.website.insert(END, '\n')
                        self.container_stack.append(frame)

                    elif element.name == '/div':
                        if len(self.container_stack) > 1:
                            self.container_stack.pop()

                    elif element.name == 'h1':
                        Label(self.container_stack[-1], text=element.get_text(), font=Font(size=32), wraplength=self.screen_width * 1.5 - 20).pack()

                    elif element.name == 'h2':
                        Label(self.container_stack[-1], text=element.get_text(), font=Font(size=24), wraplength=self.screen_width * 1.5 - 20).pack()

                    elif element.name == 'p':
                        Label(self.container_stack[-1], text=element.get_text(), font=Font(size=16), wraplength=self.screen_width * 1.5 - 20).pack()

                    elif element.name == 'a':
                        button = Label(self.container_stack[-1], text=element.get_text().strip(), fg='blue', font=Font(size=16))
                        button.pack()

                        def _redirect_from_hyperlink(url):
                            self.addressbar.delete(0, END)
                            self.addressbar.insert(END, url)
                            self.get_website(event=True)

                        href = element.get('href')
                        if href.startswith('/'):
                            href = f"https://{url.split('/')[2]}{href}"
                        elif not href.startswith('http'):
                            href = f"https://{url.split('/')[2]}/{href.strip('/')}"

                        button.bind("<Button>", lambda event=None, url=href: _redirect_from_hyperlink(url))
                        button.bind("<Enter>", lambda event, btn=button: btn.config(font=Font(underline=True, size=16)))
                        button.bind("<Leave>", lambda event, btn=button: btn.config(font=Font(underline=False, size=16)))

                    elif element.name == 'img':
                        src = element.get('src')
                        if src.startswith('/'):
                            src = f"https://{url.split('/')[2]}{src}"
                        elif not src.startswith('http'):
                            src = f"https://{url.split('/')[2]}/{src.strip('/')}"

                        self.website.insert(insert_position, '\n', 'p')
                        self.download_image(src, insert_position)

                cng = "WyJZb3Ugc2hvdWxkIHRoYW5rIGhlciEiLCAiR2l2ZSBoZXIgYSBodWchIiwgIkRhbmNlIHBhcnR5ISIsICJZYXkhIiwgIkNvbmdyYXR1bGF0ZSBoZXIhIiwgIkNyYXp5LCByaWdodCEiLCAiVGhhdCdzIHNvbWUgZ3JlYXQgc3R1ZmYgdGhlcmUhIiwgIllvdSBzaG91bGQgZ2V0IHNvbWUgcGl6emEgaW4gY2VsZWJyYXRpb24iLCAiVGVsbCB5b3VyIG1hbWFhIl0="
                print(f'[{round(time.time())}] Rescence took {time.time()-starttime} to display site {url}. {random.choice(json.loads(base64.b64decode(cng)))}')

            except requests.exceptions.ConnectionError as e:
                self.website.insert(END, e)
                print(f'[{round(time.time())}] Failure to connect to site {url}. Rescence took {time.time()-starttime}')

            except (requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema) as e:
                self.website.insert(END, e)
                print(f'[{round(time.time())}] That`s a weird URL! Rescence took {time.time()-starttime}')

                
            self.website.config(state='disabled')

        threading.Thread(target=_get_website, args=(event,), daemon=True).start()


    def download_image(self, img_url, insert_position):
        def _download_image():
            try:
                print(f"[{round(time.time())}] Rescence is getting image...")

                response = self.session.get(img_url)
                image = PILImage.open(io.BytesIO(response.content))
                photo = ImageTk.PhotoImage(image)

                image_label = Label(self.container_stack[-1], image=photo)

                image_label.pack(padx=10, pady=5, fill='x')

                self.images.append(photo)
            except Exception as e:
                print(f"[{round(time.time())}] Rescence failed to get image! {e}")
                
        threading.Thread(target=_download_image, daemon=True).start()

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            url = self.history[self.history_index]
            self.addressbar.delete(0, END)
            self.addressbar.insert(END, url)
            self.get_website()

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            url = self.history[self.history_index]
            self.addressbar.delete(0, END)
            self.addressbar.insert(END, url)
            self.get_website()

    def get_refresh(self, event=None):
        if self.history and self.history_index >= 0:
            url = self.history[self.history_index]
            self.addressbar.delete(0, END)
            self.addressbar.insert(END, url)
            self.get_website()

    def save_current_page(self, event=None):
        url: str = self.history[self.history_index]
        conent = self.session.get(url).text

        with open(f'{time.time()}.html', 'w') as file:
            file.write(conent)

    def save_current_page_as(self, event=None):
        url: str = self.history[self.history_index]
        conent = self.session.get(url).text

        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])

        with open(filename, 'w') as file:
            file.write(conent)

if __name__ == "__main__":
    master = Tk()
    app = RescenceWebBrowser(master)
    master.mainloop()

    input('Browser has finished! Enter anything to terminate: ')
