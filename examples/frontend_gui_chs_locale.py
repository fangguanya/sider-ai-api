import sys,os,_thread,functools
from warnings import warn
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import tkinter.scrolledtext as scrolledtext
from sider_ai_api import Session,MODELS,ADVANCED_MODELS

CHAT_MODES={
    "聊天":Session.chat,
    "搜索":Session.search,
    "翻译":Session.translate,
    "语法检查 (英文)":Session.improve_grammar,
}
class RedirectedStream:
    def __init__(self,text,tag,autoflush=False):
        self.text=text
        self.tag=tag
        self.autoflush=autoflush
    def write(self,string):
        self.text.insert(tk.END,string,self.tag) # 输出文字
        #self.text.mark_set("insert",END) # 将光标移到文本末尾，以显示新输出的内容
        if self.autoflush:self.flush()
    def flush(self):
        self.text.see(tk.END) # self.text.yview('moveto',1)
        self.text.update()

class ScrolledText(scrolledtext.ScrolledText):
    # 避免文本框的state属性为DISABLED时，无法插入和删除
    def __init__(self,*args,**kw):
        self.__super=super() # 提高性能
        self.__super.__init__(*args,**kw)
    # pylint: disable=no-self-argument, no-member
    def _wrapper(func):
        @functools.wraps(func)
        def inner(self,*args,**kw):
            disabled = self["state"]==tk.DISABLED
            if disabled:
                self.config(state=tk.NORMAL)
            result=getattr(self.__super,func.__name__)(*args,**kw)
            if disabled:
                self.config(state=tk.DISABLED)
            return result
        return inner
    @_wrapper
    def insert(self,*args,**kw):pass
    @_wrapper
    def delete(self,*args,**kw):pass

SEPARATOR="---"
class SiderGUI(tk.Tk):
    TITLE="sider.ai 图形界面调用工具"
    FONT=(None,11,"normal")
    ICON="sider.ico"
    def __init__(self):
        super().__init__()
        self.title(self.TITLE)
        self.geometry("1000x800")  # 设置窗口大小
        self.protocol("WM_DELETE_WINDOW", self.exit)
        icon_file=os.path.join(os.path.split(__file__)[0],self.ICON)
        if os.path.isfile(icon_file):
            self.iconbitmap(icon_file)

        # 初始化属性，以及默认设置
        self.model="gpt-4o-mini"
        self.mode_func=Session.chat
        self.original_stdout=self.original_stderr=None
        self.session = Session(update_info_at_init=False)

        top_frame=tk.Frame(self)
        top_frame.pack(side=tk.TOP,fill=tk.X)
        self.lbl_remain=tk.Label(top_frame)
        self.lbl_remain.pack(side=tk.RIGHT)

        # 创建主聊天记录框
        self.chat_display = ScrolledText(self,wrap=tk.WORD,state=tk.DISABLED,font=self.FONT)
        self.chat_display.tag_config("ai_resp", justify="left")
        self.chat_display.tag_config("user", justify="right")
        self.chat_display.tag_config("output", justify="left")
        self.chat_display.tag_config("error", justify="left", foreground="red")

        # 创建用户输入框
        self.user_input = ScrolledText(self, wrap=tk.WORD, height=5, font=self.FONT)

        bottom_frame = tk.Frame(self)
        style = ttk.Style()
        style.configure("TMenubutton", background="#CCCCCC") # 设置OptionMenu为灰色

        mode_var=tk.StringVar()
        default_mode=[k for k,v in CHAT_MODES.items() if v == self.mode_func][0]
        self.mode_select = ttk.OptionMenu(bottom_frame, mode_var, default_mode, *tuple(CHAT_MODES),
                                command=lambda event:setattr(self,"mode_func",CHAT_MODES[mode_var.get()]))
        self.mode_select.pack(side=tk.LEFT, padx=5)
        model_var=tk.StringVar()
        models=MODELS+[SEPARATOR]+ADVANCED_MODELS
        def on_select_model(event):
            model=model_var.get()
            if model==SEPARATOR:
                msgbox.showinfo("",f"无效选项: {model}，请重新选择!")
            self.model=model
        self.model_select = ttk.OptionMenu(bottom_frame, model_var, self.model, *models,
                                           command=on_select_model)
        self.model_select.pack(side=tk.LEFT, padx=5)

        self.new_chat_button = ttk.Button(bottom_frame, text="新对话",
                                          command=self.new_chat)
        self.new_chat_button.pack(side=tk.RIGHT, padx=5)
        self.send_button = ttk.Button(bottom_frame, text="发送",
                                      command=self.send_message)
        self.bind_all("<Control-Return>",self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)

        bottom_frame.pack(side=tk.BOTTOM,fill=tk.X)
        self.user_input.pack(side=tk.BOTTOM,fill=tk.X)
        self.chat_display.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.redirect_stream()
        self.update()

        try:self.session.update_userinfo()
        except Exception as err:
            warn(f"Failed to get user info ({type(err).__name__}): {err}")
        self.update_remain()
    def redirect_stream(self): # 重定向sys.stdout和sys.stderr
        self.original_stdout=sys.stdout
        self.original_stderr=sys.stderr
        sys.stdout=RedirectedStream(self.chat_display,"output")
        sys.stderr=RedirectedStream(self.chat_display,"error")
    def reset_stream(self):
        sys.stdout=self.original_stdout
        sys.stderr=self.original_stderr
    def exit(self):
        self.reset_stream()
        self.destroy()

    def update_remain(self):
        self.lbl_remain["text"]=f"""基础: 剩余 {self.session.remain or 0}/{self.session.total or 0} \
高级: 剩余 {self.session.advanced_remain or 0}/{self.session.advanced_total or 0}"""

    def new_chat(self):
        # 清空聊天记录并开始新对话
        self.chat_display.delete(1.0, tk.END)
        self.session.context_id = ""  # 重置对话上下文

    def send_message(self,event=None):
        # 发送用户输入的内容并处理 AI 回复
        user_message = self.user_input.get(1.0, tk.END).strip()
        if not user_message:
            return  # 如果输入为空，则不发送

        # 将用户消息显示在主聊天框中（右对齐）
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"你: \n{user_message}\n", "user")
        self.chat_display.insert(tk.END, f"{self.model}:\n", "ai")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)  # 滚动到底部

        # 清空用户输入框
        self.user_input.delete(1.0, tk.END)

        # 启动线程处理 AI 回复
        _thread.start_new_thread(self.get_ai_response, (user_message,))

    def get_ai_response(self, user_message):
        # 调用 Sider API 获取 AI 回复
        try:
            for response in self.mode_func(self.session,user_message,model=self.model):
                self.chat_display.insert(tk.END, response, "ai_resp")
                self.chat_display.see(tk.END)  # 滚动到底部
            self.chat_display.insert(tk.END, "\n", "ai_resp")
            self.chat_display.see(tk.END)
        except Exception as err:
            print(f"{type(err).__name__}: {err}\n", file=sys.stderr)
        self.update_remain()

def hdpi_support():
    if sys.platform == 'win32': # Windows下的高DPI支持
        try:
            import ctypes
            PROCESS_SYSTEM_DPI_AWARE = 1
            ctypes.OleDLL('shcore').SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE)
        except (ImportError, AttributeError, OSError):
            pass

if __name__ == "__main__":
    hdpi_support()
    app = SiderGUI()
    app.mainloop()