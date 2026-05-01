from pathlib import Path

base_dir = Path('.')

for file_path in base_dir.rglob('*'):
	if file_path.is_file():
		folder_name = file_path.parent.name
		new_name = f"{file_path.stem}_{folder_name}{file_path.suffix}"
		new_path = file_path.parent / new_name
		if file_path.name != new_name:
			print(f"Renaming: {file_path.name} -> {new_name}")
			file_path.rename(new_path)