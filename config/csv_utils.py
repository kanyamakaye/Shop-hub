import csv

from django.http import HttpResponse


def csv_response(filename, header, rows):
    """Builds a downloadable CSV HttpResponse from a header row and an iterable of row lists."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    writer.writerows(rows)
    return response
