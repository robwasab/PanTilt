import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import glob


files = sorted(
   glob.glob('*.jpg')
)

print(files)

num_files = len(files)

num_rows = max(1, num_files // 3)

plt.figure(figsize=(15, 5 * num_rows))


for index in range(num_files):
   filename = files[index]

   color = filename.split('__')[0]

   ax = plt.subplot(num_rows, 3, index + 1)

   img = mpimg.imread(files[index])

   ax.imshow(img)
   ax.get_xaxis().set_visible(False)
   ax.get_yaxis().set_visible(False)

   ax.set_title(color)


plt.tight_layout()
plt.show()



