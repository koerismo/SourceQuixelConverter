from .lib.pbr.src.module.core.material import Material, MaterialMode, GameTarget, NormalType
from .lib.pbr.src.module.core.io.image import Image
from .lib.pbr.src.module.core.texops import normalize
from .lib.pbr.src.module.core.io.imio import ImIOBackend
from .read_meta import QuixelAsset, QuixelTexture
from pathlib import Path

Image.set_backend(ImIOBackend)

def _load_texture(path: Path, asset: QuixelAsset, tex: str, mode: str|None=None):
	if tex not in asset.textures: return None
	tex_path = path / asset.textures[tex].path
	if not tex_path.exists(): return None
	return normalize(Image.load(tex_path), mode=mode)

def make_material(path: Path, asset: QuixelAsset, texSize=(2048, 2048)):
	use_envmap = asset.textures["Roughness"].minIntensity < 0.6
	TEX_SIZE = texSize

	folder = path.parent

	mat = Material(
		MaterialMode.PhongEnvmap if use_envmap else MaterialMode.Phong,
		GameTarget.V2011,
		TEX_SIZE,
		TEX_SIZE,
		str(Path("models") / asset.materialName),
		_load_texture(folder, asset, "Albedo"),
		_load_texture(folder, asset, "Roughness", "L"),
		_load_texture(folder, asset, "Metalness", "L"),
		_load_texture(folder, asset, "Transmission", "RGB"),
		_load_texture(folder, asset, "AO", "L"),
		_load_texture(folder, asset, "Normal", "RGB"),
		_load_texture(folder, asset, "Displacement", "L"),
		NormalType.GL
	)

	if mat.metallic is None:
		mat.metallic = Image.blank(TEX_SIZE, (0.0,))

	return mat