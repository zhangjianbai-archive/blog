"""Import only publishable HTML and metadata from a reviewed package, never originals."""
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath


def import_package(package, destination):
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        manifests = [name for name in names if PurePosixPath(name).name == 'manifest.json']
        assert len(manifests) == 1, 'Expected exactly one manifest'
        manifest_name = manifests[0]
        records = json.loads(archive.read(manifest_name).decode('utf-8-sig'))
        assert isinstance(records, list)
        base = PurePosixPath(manifest_name).parent
        pending = []
        for record in records:
            assert record['status'] in {'publish', 'hold'}
            if record['status'] != 'publish':
                record['html_file'] = ''
                continue
            relative = PurePosixPath(record['html_file'])
            assert not relative.is_absolute() and '..' not in relative.parts
            assert relative.suffix == '.html'
            content = archive.read(str(base / relative)).decode('utf-8-sig')
            target = (destination / str(relative)).resolve()
            assert target.is_relative_to(destination.resolve())
            pending.append((target, content))
        destination.mkdir(parents=True, exist_ok=True)
        for target, content in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        (destination / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Imported {len(pending)} HTML documents; {len(records)-len(pending)} held; no raw attachments imported.')


if __name__ == '__main__':
    import_package(Path(sys.argv[1]), Path(__file__).resolve().parents[1] / 'content/internal')
