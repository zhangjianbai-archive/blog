"""Apply manually checked paragraph joins and structural heading decisions."""
import json
from pathlib import Path
from review_markdown import create, apply

ROOT = Path(__file__).resolve().parents[1]

# Paragraph numbers refer to the supplied original DOCX, not rendered headings.
JOINS = {
    '0084': [[90,91],[105,106],[116,117]],
    '0133': [[137,138],[141,142],[152,153],[158,159]],
    '0449': [[454,455],[467,468,469],[474,475]],
    '0480': [[494,495,496],[515,516,517]],
    '0529': [[533,534],[535,536],[542,543],[547,548],[549,550],[561,562]],
    '0592': [[595,596],[602,603,604],[606,607,608],[617,618]],
    '0640': [[646,647],[667,668,669]],
    '0699': [[706,707]],
    '0752': [[755,756],[758,759],[769,770]],
    '0819': [[824,825],[826,827],[846,847],[857,858],[859,860]],
    '0870': [[875,876],[886,887],[896,897],[898,899],[901,902]],
    '0915': [[918,919],[930,931]],
}
HEADINGS = {
    '0084': {90:2,98:2,110:2,122:2},
    '0133': {139:2,146:2,150:2,156:2},
    '0411': {423:2,431:2,439:2},
    '0449': {456:2,464:2,471:2},
    '0480': {485:2,489:3,491:3,493:3,498:2,503:3,505:3,507:3,510:2,524:2},
    '0529': {538:2,544:2,552:2,558:2,565:2,571:2,574:3,576:3,578:3,583:3,585:3},
    '0592': {599:2,610:2,617:2,624:2,626:3,628:3,631:3},
    '0752': {758:2,771:2},
    '0819': {826:2,835:2,843:2,851:2},
    '0870': {877:2,884:2,892:2,895:3,898:3,901:3},
    '0915': {922:2,930:2,938:2},
}
POINTS = {'0084':[2,3], '0133':[2,4], '0411':[1,2], '0449':[1,3],
          '0480':[5,9], '0529':[5,10], '0592':[2,7], '0752':[1,2],
          '0819':[1,4], '0870':[3,6], '0915':[2,3]}

for suffix in sorted(set(JOINS) | set(HEADINGS)):
    path = ROOT/'review'/f'07-{suffix}-config.json'
    config = json.loads(path.read_text(encoding='utf-8'))
    if suffix in JOINS:
        config['merge_paragraphs'] = JOINS[suffix]
    if suffix in HEADINGS:
        config['headings'] = {str(k):v for k,v in HEADINGS[suffix].items()}
        config.pop('section_titles', None)
    for point, section in zip(config['key_points'], POINTS.get(suffix, [])):
        point['section'] = section
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    output = ROOT/'content/posts'/f'collection-07-{suffix}.md'
    create(ROOT/'review/source-07.json', path, output)
    apply(output)
    print(f'Reviewed collection-07-{suffix}')
