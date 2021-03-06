#!/usr/bin/python
# -*- coding: UTF-8 -*-
#Author zhang
import tensorflow as tf
from tensorflow.keras.layers import Dense, Embedding, Conv2D, Dropout, Flatten, MaxPool2D, concatenate
import numpy as np

class Config(object):

    """配置参数"""
    def __init__(self, dataset, embedding):
        self.model_name = 'TextCNN2D'
        self.train_path = dataset + '/data/train.txt'                                # 训练集
        self.dev_path = dataset + '/data/dev.txt'                                    # 验证集
        self.test_path = dataset + '/data/test.txt'                                  # 测试集
        self.class_list = [x.strip() for x in open(
            dataset + '/data/class.txt').readlines()]                                # 类别名单
        self.vocab_path = dataset + '/data/vocab.pkl'                                # 词表
        self.save_path = dataset + '/saved_dict/' + self.model_name + '.h5'        # 模型训练结果
        self.log_path = dataset + '/log/' + self.model_name
        self.embedding_pretrained = np.load(dataset + '/data/' + embedding)["embeddings"].astype('float32')\
            if embedding != 'random' else None                                       # 预训练词向量

        self.dropout = 0.5                                              # 随机失活
        self.require_improvement = 1000                                 # 若超过1000batch效果还没提升，则提前结束训练
        self.num_classes = len(self.class_list)                         # 类别数
        self.n_vocab = 0                                                # 词表大小，在运行时赋值
        self.num_epochs = 20                                            # epoch数
        self.batch_size = 128                                           # mini-batch大小
        self.max_len = 32                                              # 每句话处理成的长度(短填长切)
        self.learning_rate = 1e-3                                       # 学习率
        self.embed = self.embedding_pretrained.shape[1]\
            if self.embedding_pretrained is not None else 300           # 字向量维度
        self.filter_sizes = (2, 3, 4)                                   # 卷积核尺寸
        self.num_filters = 256                                          # 卷积核数量(channels数)

class MyModel(tf.keras.Model):
    def __init__(self, config):
        super(MyModel, self).__init__()
        self.config = config
        self.embedding = Embedding(input_dim=self.config.embedding_pretrained.shape[0], output_dim=self.config.embedding_pretrained.shape[1],
                                   input_length=self.config.max_len, weights=[self.config.embedding_pretrained], trainable=True)
        self.convs = [Conv2D(filters=config.num_filters, kernel_size=(k, config.embed), padding='valid', kernel_initializer='normal', activation='relu') for k in config.filter_sizes]
        self.pools = [MaxPool2D(pool_size=(self.config.max_len - k + 1, 1), strides=(1, 1), padding='valid') for k in config.filter_sizes]
        self.flatten = Flatten()
        self.dropout = Dropout(self.config.dropout)
        self.out_put = Dense(units=config.num_classes, activation='softmax')

    def conv_and_pool(self, x, conv, pool):
        x = conv(x)
        x = pool(x)
        return x

    def build(self, input_shape):
        super(MyModel, self).build(input_shape)

    def call(self, x):
        x = self.embedding(x)
        x = tf.expand_dims(x, axis= -1)
        x = concatenate([self.conv_and_pool(x, conv, pool) for conv, pool in zip(self.convs,self.pools)], axis=-1)
        x = self.flatten(x)
        x = self.dropout(x)
        x = self.out_put(x)
        return x
