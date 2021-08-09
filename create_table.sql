create table weibo_sent_comments
(
    page                varchar(4)  not null comment '页数',
    id                  varchar(50) not null comment 'id',
    mid                 varchar(50) not null comment '评论id',
    reply_text          text        null comment '评论内容',
    reply_original_text text        null comment '评论原内容',
    created_date        char(10)    not null comment '评论日期',
    created_time        char(19)    not null comment '评论时间',
    target_text         text        null comment '被回复的原文',
    data_json           text        not null comment '原数据json'
) comment '微博已发评论表' default character set = utf8mb4;