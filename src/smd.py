# https://developer.valvesoftware.com/wiki/SMD

# import bpy
# import mathutils
from io import TextIOBase

TEMPLATE_SMD_HEADER = '''version 1
nodes
0 "root" -1
end
skeleton
time 0
0	0 0 0	0 0 0
end
triangles
'''

TEMPLATE_VTA_HEADER = '''version 1
nodes
0 "root" -1
end
skeleton
'''

TEMPLATE_DRIVER_HEADER = '''version 1
nodes
0 "root" -1
1 "vcabone_MyAnim" -1
end
skeleton
'''

class SourceModelWriter():
	smd: TextIOBase
	vta: TextIOBase
	driver: TextIOBase

	def __init__(self, filepath: str) -> None:
		self.smd = open(filepath, 'w')
		self.smd.write(TEMPLATE_SMD_HEADER)

	def write_smd_vertex(self, vtx: tuple, nrm: tuple, uv: tuple[float, float]):
		self.smd.write(f'0	{vtx[0]} {vtx[1]} {vtx[2]}	{nrm[0]} {nrm[1]} {nrm[2]}	{uv[0]} {uv[1]}\n')

	def write_smd_triangle(self, material: str):
		self.smd.write(f'{material}\n')

	def end(self):
		self.smd.write('end')

	def close(self):
		self.smd.close()
