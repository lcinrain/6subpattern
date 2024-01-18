#python DynamicScan.py --input='../hitlist_biasedsampling.compressed.10000.txt' --output=biased --budget=100000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'

#python DynamicScan.py --input='../hitlist_biasedsampling.compressed.100000.txt' --output=biased --budget=1000000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'

python DynamicScan.py --input='../hitlist_biasedsampling.compressed.1000000.txt' --output=biased --budget=10000000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'



# python DynamicScan.py --input='../hitlist_downsampling.compressed.10000.txt' --output=down --budget=100000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'

# python DynamicScan.py --input='../hitlist_downsampling.compressed.100000.txt' --output=down --budget=1000000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'

python DynamicScan.py --input='../hitlist_downsampling.compressed.1000000.txt' --output=down --budget=10000000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'

# python DynamicScan.py --input='../hitlist_prefixsampling.compressed.10000.txt' --output=prefix --budget=100000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'

python DynamicScan.py --input='../hitlist_prefixsampling.compressed.100000.txt' --output=prefix --budget=1000000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'

python DynamicScan.py --input='../hitlist_prefixsampling.compressed.1000000.txt' --output=prefix --budget=10000000  --IPv6='2401:c080:3800:2ec8:5400:4ff:fe78:2146'
