from http.server import BaseHTTPRequestHandler,HTTPServer
import sys,os
import subprocess

class base_case(object):
	'''条件处理基类'''
	
	def handle_file(self,handler,full_path):
		try:
			with open(full_path,'rb') as reader:
				content = reader.read()
			handler.send_content(content)

		except IOError as msg:
			msg = "'{0}' can not be red:{1}".format(full_path,msg)
			handler.handle_error(msg)


	def index_path(self,handler):
		return os.path.join(handler.full_path,'index.html')


	#要求子类必须实现接口
	def test(self,handler):
		assert False,'Not implemented'

	def act(self,handler):
		assert False,'Not implemented'

class ServerException(Exception):
	'''服务器内部错误'''
	pass

class case_no_file(base_case):
	'''该路经不存在'''

	def test(self,handler):
		return not os.path.exists(handler.full_path)

	def act(self,handler):
		raise ServerException("'{0}' not found".format(handler.path))


class case_existing_file(base_case):
	'''该路经是文件'''

	def test(self,handler):
		return os.path.isfile(handler.full_path)


	def act(self,handler):
		handler.handle_file(handler.full_path)



class case_always_fail(base_case):

	'''所有情况都不符合时的默认处理类'''

	def test(self,handler):
		return True


	def act(self,handler):
		raise ServerException("Unknown object '{0}'".format(handler.path))

class case_directory_index_file(base_case):
	

		#判断目标路径是否是目录 && 目录下是否有index.html
	def test(self,handler):
		return os.path.isdir(handler.full_path) and \
			os.path.isfile(self.index_path(handler))


	#响应index.html的内容
	def act(self,handler):
		handler.handle_file(self.index_path(handler))


class case_cgi_file(base_case):
	'''脚本文件处理'''

	def run_cgi(self,handler):
		data = subprocess.check_output(["python3",handler.full_path],shell=False)
		handler.send_content(data)


	def test(self,handler):
		return os.path.isfile(handler.full_path) and \
			handler.full_path.endswith('.py')

	def act(self,handler):
		#运行脚本文件
		self.run_cgi(handler)


class RequestHandler(BaseHTTPRequestHandler):
	'''处理请求返回页面'''
	
	#页面模板
	Page = '''\
	       <html>
	       <body>
	       <table>
	       <tr> <td>Header</td>         <td>Value</td>          </tr>
	       <tr> <td>Date and time</td>  <td>{date_time}</td>    </tr>
	       <tr> <td>Client host</td>    <td>{client_host}</td>  </tr>
	       <tr> <td>Client port</td>    <td>{client_port}</td>  </tr>
	       <tr> <td>Command</td>	    <td>{command}</td>	    </tr>
	       <tr> <td>Path</td>	    <td>{path}</td>	    </tr>
	       </table>
	       </body>
	       </html>
	 '''

	Cases = [case_no_file(),case_cgi_file(),case_existing_file(),case_directory_index_file(),case_always_fail()]


	def do_GET(self):
		try:
			#文件完整路径
			self.full_path = os.getcwd()+self.path
			
			#遍历所有可能的情况
			for case in self.Cases:
				#如果满足该类情况
				if case.test(self):
					#调用相应的act函数
					case.act(self)
					break

		#处理异常
		except Exception as msg:
			self.handle_error(msg)

	def handle_file(self,full_path):
		try:
			with open(full_path,'rb') as reader:
				content = reader.read()
			self.send_content(content)

		except IOError as msg:
			msg = "'{0} cannot be read:{1}'".format(self.path,msg)
			self.handle_error(msg)



	Error_Page = """\
			<html>
			<body>
			<h1> Error accessing {path}</h1>
			<p> {msg} </p>
			<body>
			</html>
		     """


	def handle_error(self,msg):
		content = self.Error_Page.format(path=self.path,msg=msg)
		self.send_content(content.encode('utf-8'),404)


	def send_content(self,content,status=200):
		self.send_response(status)
		self.send_header("Content-Type","text/html")
		self.send_header("Content-Length",str(len(content)))
		self.end_headers()
		self.wfile.write(content)


	def create_page(self):
	    values = {
		'date_time' : self.date_time_string(),
		'client_host' : self.client_address[0],
		'client_port' : self.client_address[1],
		'command' : self.command,
		'path' : self.path
		}

	    page = self.Page.format(**values)
	    return page





if __name__ == '__main__':
	serverAddress = ('',8080)
	server = HTTPServer(serverAddress,RequestHandler)
	server.serve_forever() 





