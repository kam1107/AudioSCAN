. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

voting_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/RealWorld/final_result/voting
#nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
nnet_dir=e2e_ter1/exp/xvector_nnet_1a
orig_plda_data_dir=data/plda_v1
new_plda_dir=exp/xvectors_plda_RW_e2e_iter1

. utils/parse_options.sh

rm -rf data/voting
local/make_audioscan_voting.pl $voting_root data/voting

###combine associated data with the original PLDA training data
rm -rf data/plda_tune
utils/combine_data.sh data/plda_tune $orig_plda_data_dir data/voting

# Make MFCCs and compute the energy-based VAD for each dataset
steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 50 --cmd "$train_cmd" \
    data/plda_tune exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/plda_tune

sid/compute_vad_decision.sh --nj 50 --cmd "$train_cmd" \
    data/plda_tune exp/make_vad $vaddir
utils/fix_data_dir.sh data/plda_tune


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 100 \
  $nnet_dir data/plda_tune \
  $new_plda_dir


# update mean
$train_cmd $new_plda_dir/log/compute_mean.log \
  ivector-mean scp:$new_plda_dir/xvector.scp \
  $new_plda_dir/mean.vec || exit 1;

# update PLDA model
lda_dim=200
$train_cmd $new_plda_dir/log/lda.log \
  ivector-compute-lda --total-covariance-factor=0.0 --dim=$lda_dim \
  "ark:ivector-subtract-global-mean scp:$new_plda_dir/xvector.scp ark:- |" \
  ark:data/plda_tune/utt2spk $new_plda_dir/transform.mat || exit 1;

$train_cmd $new_plda_dir/log/plda.log \
  ivector-compute-plda ark:data/plda_tune/spk2utt \
  "ark:ivector-subtract-global-mean scp:$new_plda_dir/xvector.scp ark:- | transform-vec $new_plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:-  ark:- |" \
  $new_plda_dir/plda || exit 1;
