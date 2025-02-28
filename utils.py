import os

import numpy as np
import cv2
import math
import torch


def calculate_psnr(img1, img2, border=0):
    # img1 and img2 have range [0, 255]
    if not img1.shape == img2.shape:
        raise ValueError('Input images must have the same dimensions.')
    h, w = img1.shape[:2]
    img1 = img1[border:h - border, border:w - border]
    img2 = img2[border:h - border, border:w - border]

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    mse = np.mean((img1 - img2) ** 2)
    if mse < 1e-10:
        return 100
    return 20 * math.log10(255.0 / math.sqrt(mse))


# ----------
# SSIM
# ----------
def calculate_ssim(img1, img2, border=0):
    '''calculate SSIM
    the same outputs as MATLAB's
    img1, img2: [0, 255]
    '''
    if not img1.shape == img2.shape:
        raise ValueError('Input images must have the same dimensions.')
    h, w = img1.shape[:2]
    img1 = img1[border:h - border, border:w - border]
    img2 = img2[border:h - border, border:w - border]

    if img1.ndim == 2:
        return ssim(img1, img2)
    elif img1.ndim == 3:
        if img1.shape[2] == 3:
            ssims = []
            for i in range(3):
                ssims.append(ssim(img1, img2))
            return np.array(ssims).mean()
        elif img1.shape[2] == 1:
            return ssim(np.squeeze(img1), np.squeeze(img2))
    else:
        raise ValueError('Wrong input image dimensions.')


def ssim(img1, img2):
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]  # valid
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) *
                                                            (sigma1_sq + sigma2_sq + C2))
    return ssim_map.mean()


def cal_mean_performance(image_batch, performance_fn):
    performance_score_list = []
    for image_seq in image_batch:
        image_seq = image_seq.detach().cpu().numpy()
        image_seq = np.transpose(image_seq, [1, 2, 3, 0])
        for img_idx in range(image_seq.shape[0]-1):
            performance_score_list.append(performance_fn(image_seq[img_idx], image_seq[img_idx+1]))
    return sum(performance_score_list) / len(performance_score_list)


def save_important_info(loss, g, global_step, checkpoint_dir, mode='train'):
    loss_txt_path = os.path.join(checkpoint_dir, f'{mode}_loss.txt')
    if os.path.exists(loss_txt_path):
        os.remove(loss_txt_path)
    with open(loss_txt_path, 'a') as loss_txt:
        loss_txt.write(f'{global_step} {torch.mean(loss) if mode=="train" else loss}\n')
    psnr_txt_path = os.path.join(checkpoint_dir, f'{mode}_psnr.txt')
    if os.path.exists(psnr_txt_path):
        os.remove(psnr_txt_path)
    with open(psnr_txt_path, 'a') as psnr_txt:
        psnr_txt.write(f'{global_step} {cal_mean_performance(g, calculate_psnr)} \n')
    ssim_txt_path = os.path.join(checkpoint_dir, f'{mode}_ssim.txt')
    if os.path.exists(ssim_txt_path):
        os.remove(ssim_txt_path)
    with open(ssim_txt_path, 'a') as ssim_txt:
        ssim_txt.write(f'{global_step} {cal_mean_performance(g, calculate_ssim)} \n')
