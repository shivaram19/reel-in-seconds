#!/bin/bash
# Download all 8 WhatsApp images from Azure Blob Storage
# Run: bash download_images.sh

set -e

mkdir -p whatsapp_images
cd whatsapp_images

echo "Downloading 8 images..."

curl -fsSL -o "img1.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.33-%281%29-1780503633256.jpeg?se=2026-06-10T16%3A20%3A35Z&sp=r&sv=2026-04-06&sr=b&sig=BK7rFNUNtFtDe2TWtPK8NZCeBQFx91ZQOBmE8mGkb6s%3D"
echo "✓ img1.jpeg"

curl -fsSL -o "img2.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.33-%282%29-1780503635734.jpeg?se=2026-06-10T16%3A20%3A36Z&sp=r&sv=2026-04-06&sr=b&sig=xRBLRRjkL/cHpKxLjXuZOb218xNtLITxP7RI/AtgDuU%3D"
echo "✓ img2.jpeg"

curl -fsSL -o "img3.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.33-1780503637007.jpeg?se=2026-06-10T16%3A20%3A38Z&sp=r&sv=2026-04-06&sr=b&sig=/SqSQOg1T79qKFwLYIFhmW7q8HJWXjfy844vo2bh/xs%3D"
echo "✓ img3.jpeg"

curl -fsSL -o "img4.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.34-%281%29-1780503638341.jpeg?se=2026-06-10T16%3A20%3A39Z&sp=r&sv=2026-04-06&sr=b&sig=OYgpFLN6A/U0LdBKttPVe2IKSS4WWnnq/7oOTB3zXrA%3D"
echo "✓ img4.jpeg"

curl -fsSL -o "img5.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.34-%282%29-1780503639505.jpeg?se=2026-06-10T16%3A20%3A40Z&sp=r&sv=2026-04-06&sr=b&sig=kSSXxS9RGe5vaJtOf3LLaU3brTh9ubyHQxMb7FlpNIQ%3D"
echo "✓ img5.jpeg"

curl -fsSL -o "img6.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.34-1780503640653.jpeg?se=2026-06-10T16%3A20%3A41Z&sp=r&sv=2026-04-06&sr=b&sig=t8EIxV9/hkQO/wwdJXHtUsRY7yTtUJsGOYPHaZSE3hE%3D"
echo "✓ img6.jpeg"

curl -fsSL -o "img7.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.35-%281%29-1780503641761.jpeg?se=2026-06-10T16%3A20%3A42Z&sp=r&sv=2026-04-06&sr=b&sig=biRwwPZtyQSsKCxvXv33qSd2OEHpYtxbrWO0kKEL3bQ%3D"
echo "✓ img7.jpeg"

curl -fsSL -o "img8.jpeg" "https://mediastore3146.blob.core.windows.net/media/dev-workstation/images/WhatsApp-Image-2026-06-03-at-19.29.35-1780503642768.jpeg?se=2026-06-10T16%3A20%3A43Z&sp=r&sv=2026-04-06&sr=b&sig=%2B/VPDS0ghLYwy5JimeK%2BAvxcsP%2BhJ4U/EeZKEEOSRx8%3D"
echo "✓ img8.jpeg"

echo ""
echo "All 8 images downloaded to ./whatsapp_images/"
ls -la
