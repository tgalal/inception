FROM base/archlinux
RUN pacman -Syy
RUN pacman --noconfirm -S git
RUN pacman --noconfirm -S binutils
RUN pacman --noconfirm -S sudo
RUN pacman --noconfirm -S gcc
RUN pacman --noconfirm -S pkg-config
RUN pacman --noconfirm -S make 
RUN pacman --noconfirm -S fakeroot 

RUN mkdir /home/build &&\
    useradd build &&\
    usermod -L build &&\
    chown build:build /home/build

WORKDIR /home/build

RUN echo "build ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN echo "root ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER build

RUN  git clone https://aur.archlinux.org/package-query.git
WORKDIR package-query
RUN makepkg -si --noconfirm
WORKDIR ..

USER build
RUN git clone https://aur.archlinux.org/yaourt.git
WORKDIR yaourt
RUN makepkg -si --noconfirm
WORKDIR ..

RUN yaourt -S inception-android --noconfirm

ENTRYPOINT ["incept"]
