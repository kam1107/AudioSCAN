. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

new_plda_dir=exp/meanshift_plda_audioscan_diaseg_corrupted

. utils/parse_options.sh

# update mean
$train_cmd $new_plda_dir/log/compute_mean.log \
  ivector-mean scp:exp/xvectors_audioscan_diaseg_corrupted/xvector.scp \
  $new_plda_dir/mean.vec || exit 1;
