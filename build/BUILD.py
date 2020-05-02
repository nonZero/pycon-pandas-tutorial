"""Build the tutorial data files from the IMDB *.list.gz files."""

import csv
import gzip
import os
import re
from datetime import datetime

split_on_tabs = re.compile('\t+').split


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir('../data'):
        os.makedirs('../data')

    # Load movie titles.

    titles = set()
    uninteresting_titles = set()

    lines = iter(gzip.open('genres.list.gz', encoding="iso8859-1", mode="rt"))
    line = next(lines)
    while line != '8: THE GENRES LIST\n':
        line = next(lines)
    assert next(lines) == '==================\n'
    assert next(lines) == '\n'

    print('Reading "genres.list.gz" to find interesting movies')

    for line in lines:
        if not_a_real_movie(line):
            continue

        fields = split_on_tabs(line.strip('\n'))
        raw_title = fields[0]
        genre = fields[1]

        if genre in ('Adult', 'Documentary', 'Short'):
            uninteresting_titles.add(raw_title)
        else:
            titles.add(raw_title)

    interesting_titles = titles - uninteresting_titles
    del titles
    del uninteresting_titles

    print('Found {0} titles'.format(len(interesting_titles)))

    print('Writing "titles.csv"')

    with open('../data/titles.csv', 'w') as f:
        output = csv.writer(f)
        output.writerow(('title', 'year'))
        for raw_title in sorted(interesting_titles):
            title_and_year = parse_title(raw_title)
            output.writerow(title_and_year)

    print('Finished writing "titles.csv"')
    print('Reading release dates from "release-dates.list.gz"')

    lines = iter(gzip.open('release-dates.list.gz', encoding='iso-8859-1', mode="rt"))
    line = next(lines)
    while line != 'RELEASE DATES LIST\n':
        line = next(lines)
    assert next(lines) == '==================\n'

    output = csv.writer(open('../data/release_dates.csv', 'w'))
    output.writerow(('title', 'year', 'country', 'date'))

    for line in lines:
        if not_a_real_movie(line):
            continue

        if line.startswith('----'):
            continue

        fields = split_on_tabs(line.strip('\n'))
        if len(fields) > 2:     # ignore "DVD premier" lines and so forth
            continue

        raw_title = fields[0]
        if raw_title not in interesting_titles:
            continue

        title, year = parse_title(raw_title)
        if title is None:
            continue

        country, datestr = fields[1].split(':')
        try:
            date = datetime.strptime(datestr, '%d %B %Y').date()
        except ValueError:
            continue  # incomplete dates like "April 2014"
        output.writerow((title, year, country, date))

    print('Finished writing "release_dates.csv"')

    output = csv.writer(open('../data/cast.csv', 'w'))
    output.writerow(('title', 'year', 'name', 'type', 'character', 'n'))

    for role_type, filename in (
            ('actor', 'actors.list.gz'),
            ('actress', 'actresses.list.gz'),
            ):
        print('Reading {0!r}'.format(filename))
        lines = iter(gzip.open(filename, encoding="iso-8859-1", mode="rt"))

        line = next(lines)
        while ('Name' not in line) or ('Titles' not in line):
            line = next(lines)

        assert '----' in next(lines)

        for line in lines:
            if line.startswith('----------------------'):
                break

            line = line.rstrip()
            if not line:
                continue

            fields = split_on_tabs(line.strip('\n'))
            if fields[0]:
                name = fields[0]
                name = swap_names(name)

            if len(fields) < 2:
                raise ValueError('broken line: {!r}'.format(line))

            if not_a_real_movie(fields[1]):
                continue

            fields = fields[1].split('  ')
            raw_title = fields[0]
            if raw_title not in interesting_titles:
                continue

            if len(fields) < 2:
                continue

            if fields[1].startswith('('):  # uncredited, archive footage, etc
                del fields[1]
                if len(fields) < 2:
                    continue

            if not fields[1].startswith('['):
                continue

            character = fields[1].strip('[]')

            if len(fields) > 2 and fields[2].startswith('<'):
                n = int(fields[2].strip('<>'))
            else:
                n = ''

            title, year = parse_title(raw_title)
            if title is None:
                continue

            if character == 'N/A':
                clist = ['(N/A)']
            else:
                clist = character.split('/')

            for character in clist:
                if not character:
                    continue
                output.writerow((title, year, name, role_type, character, n))

    print('Finished writing "cast.csv"')


def not_a_real_movie(line):
    return (
        line.startswith('"')       # TV show
        or '{' in line             # TV episode
        or ' (????' in line        # Unknown year
        or ' (TV)' in line         # TV Movie
        or ' (V)' in line          # Video
        or ' (VG)' in line         # Video game
        )


match_title = re.compile(r'^(.*) \((\d+)(/[IVXL]+)?\)$').match


def parse_title(title):
    m = match_title(title)
    title = m.group(1)
    year = int(m.group(2))
    numeral = m.group(3)

    if numeral is not None:
        numeral = numeral.strip('/')
        if numeral != 'I':
            title = '{0} ({1})'.format(title, numeral)

    return title, year


def swap_names(name):
    if name.endswith(' (I)'):
        name = name[:-4]
    if ',' in name:
        last, first = name.split(',', 1)
        name = first.strip() + ' ' + last.strip()
    return name




if __name__ == '__main__':
    main()
