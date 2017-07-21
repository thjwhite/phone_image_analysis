import os
import cv2

IOS_READY = '.images/ios_ready'
ANDROID_READY = '.images/android_ready'
NON_PHONE_READY = '.images/non_ready'

def process(classification, identifier):
    img = cv2.imread('.images/%s/%s' % (classification, identifier))
    if img is None:
        print('ERROR')
        return
    resized = cv2.resize(img, (128, 128), interpolation=cv2.INTER_AREA)
    grayscaled = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    for rot_degree in [0, 90, 180, 270]:
        rot_matrix = cv2.getRotationMatrix2D((64, 64), rot_degree, 1)
        rotated = cv2.warpAffine(grayscaled, rot_matrix, (128, 128))
        cv2.imwrite('.images/%s_ready/%s_rot%s.png' % (classification, identifier, rot_degree), rotated)

def main():
    if not os.path.exists(IOS_READY):
        os.makedirs(IOS_READY)
    if not os.path.exists(ANDROID_READY):
        os.makedirs(ANDROID_READY)
    if not os.path.exists(NON_PHONE_READY):
        os.makedirs(NON_PHONE_READY)

    print('PROCESSING IOS IMAGES')
    images = os.listdir('.images/ios')
    for i, ios_image in enumerate(images):
        print('%s -- %d%%' % (ios_image, 100 * i / len(images)))
        process('ios', ios_image)

    print('PROCESSING ANDROID IMAGES')
    images = os.listdir('.images/android')
    for i, android_image in enumerate(images):
        print('%s -- %d%%' % (android_image, 100 * i / len(images)))
        process('android', android_image)

    print('PROCESSING NON PHONE IMAGES')
    images = os.listdir('.images/non')
    for i, non_phone_image in enumerate(images):
        print('%s -- %d%%' % (non_phone_image, 100 * i / len(images)))
        process('non', non_phone_image)


if __name__ == "__main__":
    main()
