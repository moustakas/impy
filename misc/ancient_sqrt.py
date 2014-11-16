def ancient_sqrt(n):
    approx = n/2.0
    better = (approx + n/approx)/2.0
    print better
    while better != approx:
        approx = better
        better = (approx + n/approx)/2.0
    print approx

