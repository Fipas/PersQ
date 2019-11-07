class Test:
	def __init__(self, num):
		self.num = num

t = Test(1)
tt = []
tt.append(t)

print tt[0].num

t.num = 3

print tt[0].num